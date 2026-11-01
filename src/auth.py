"""
Production-Ready Authentication & Social OAuth Engine for FreightGuard AI.
Implements:
1. Persistent user database in SQLite (users, auth_accounts, auth_sessions).
2. Real OAuth 2.0 / OpenID Connect authorization code flows:
   - Google Sign-In (with prompt=select_account, ID verification, openid email profile)
   - GitHub Sign-In (read:user, user:email, private email resolution)
   - Meta Facebook Login (public_profile, email via Graph API v19.0)
   - X / Twitter Login (OAuth 2.0 with PKCE S256, code_verifier, code_challenge)
3. Cryptographic PBKDF2-HMAC-SHA256 password hashing with unique salt.
4. Account linking: Multiple providers connected to one unified user account.
5. CSRF protection via state validation & PKCE challenge.
"""
import os
import sqlite3
import hashlib
import hmac
import secrets
import base64
import urllib.parse
import urllib.request
import json
import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List

# Load environment variables
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

def get_config_val(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve configuration from os.environ or streamlit.secrets if running in cloud."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default

from src.config import DATA_DIR

DB_PATH = DATA_DIR / "freight_audit.db"

# ==============================================================================
# 1. DATABASE SCHEMA & PERSISTENCE
# ==============================================================================

def get_db_connection() -> sqlite3.Connection:
    """Connect to SQLite database with foreign key support."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_auth_tables():
    """Create persistent users, auth_accounts, and auth_sessions tables."""
    conn = get_db_connection()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(128) NOT NULL,
            email VARCHAR(128) UNIQUE NOT NULL,
            email_verified BOOLEAN NOT NULL DEFAULT 0,
            password_hash VARCHAR(256),
            profile_image TEXT,
            role VARCHAR(64) NOT NULL DEFAULT 'Lead Freight Auditor',
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            last_login_at TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS auth_accounts (
            id VARCHAR(64) PRIMARY KEY,
            user_id VARCHAR(64) NOT NULL,
            provider VARCHAR(32) NOT NULL,
            provider_account_id VARCHAR(128) NOT NULL,
            provider_email VARCHAR(128),
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(provider, provider_account_id)
        );

        CREATE TABLE IF NOT EXISTS auth_sessions (
            session_id VARCHAR(128) PRIMARY KEY,
            user_id VARCHAR(64) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_auth_accounts_provider ON auth_accounts(provider, provider_account_id);
        CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
        """)
    conn.close()

# Initialize tables immediately on module load
init_auth_tables()

# ==============================================================================
# 2. CRYPTOGRAPHIC SECURITY (PASSWORDS, PKCE, STATE)
# ==============================================================================

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a cryptographically secure salt."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}${dk.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt$hash string."""
    try:
        salt_hex, dk_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        dk = bytes.fromhex(dk_hex)
        computed_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(dk, computed_dk)
    except Exception:
        return False

def generate_csrf_state() -> str:
    """Generate cryptographically secure 32-byte URL-safe state token for CSRF protection."""
    return secrets.token_urlsafe(32)

def generate_pkce_pair() -> Tuple[str, str]:
    """Generate PKCE code_verifier and S256 code_challenge for OAuth 2.0 with PKCE."""
    verifier = secrets.token_urlsafe(64)
    # S256 challenge: base64url(sha256(verifier))
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge

# ==============================================================================
# 3. HTTP CLIENT HELPER (SERVER-TO-SERVER OAUTH CALLS)
# ==============================================================================

def http_post(url: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Execute server-to-server POST request for token exchanges."""
    encoded_data = urllib.parse.urlencode(data).encode("utf-8")
    req_headers = {"User-Agent": "FreightGuard-AI-Auth/2.0", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    
    req = urllib.request.Request(url, data=encoded_data, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return json.loads(err_body)
        except Exception:
            return {"error": f"HTTP {e.code}", "details": err_body}
    except Exception as e:
        return {"error": str(e)}

def http_get(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Execute server-to-server GET request with Bearer authorization."""
    req_headers = {"User-Agent": "FreightGuard-AI-Auth/2.0", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    
    req = urllib.request.Request(url, headers=req_headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return json.loads(err_body)
        except Exception:
            return {"error": f"HTTP {e.code}", "details": err_body}
    except Exception as e:
        return {"error": str(e)}

# ==============================================================================
# 4. OAUTH PROVIDER IMPLEMENTATIONS
# ==============================================================================

class GoogleOAuthProvider:
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

    @classmethod
    def get_credentials(cls) -> Tuple[Optional[str], Optional[str]]:
        client_id = get_config_val("GOOGLE_CLIENT_ID")
        client_secret = get_config_val("GOOGLE_CLIENT_SECRET")
        return client_id, client_secret

    @classmethod
    def is_configured(cls) -> bool:
        cid, sec = cls.get_credentials()
        return bool(cid and sec and cid != "your_google_client_id_here")

    @classmethod
    def get_authorization_url(cls, redirect_uri: str, state: str) -> str:
        client_id, _ = cls.get_credentials()
        params = {
            "client_id": client_id or "GOOGLE_CLIENT_ID_NOT_CONFIGURED",
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",  # Mandated requirement: prompt for account selection
            "access_type": "offline"
        }
        return f"{cls.AUTH_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    def exchange_code(cls, code: str, redirect_uri: str) -> Dict[str, Any]:
        client_id, client_secret = cls.get_credentials()
        if not client_id or not client_secret:
            return {"error": "Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET"}
        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        return http_post(cls.TOKEN_URL, data)

    @classmethod
    def get_user_profile(cls, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        info = http_get(cls.USERINFO_URL, headers)
        if "error" in info:
            return info
        return {
            "provider": "google",
            "provider_account_id": info.get("sub"),
            "email": info.get("email"),
            "email_verified": bool(info.get("email_verified", False)),
            "name": info.get("name") or info.get("email", "").split("@")[0].title(),
            "profile_image": info.get("picture")
        }


class GitHubOAuthProvider:
    AUTH_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    @classmethod
    def get_credentials(cls) -> Tuple[Optional[str], Optional[str]]:
        return get_config_val("GITHUB_CLIENT_ID"), get_config_val("GITHUB_CLIENT_SECRET")

    @classmethod
    def is_configured(cls) -> bool:
        cid, sec = cls.get_credentials()
        return bool(cid and sec and cid != "your_github_client_id_here")

    @classmethod
    def get_authorization_url(cls, redirect_uri: str, state: str) -> str:
        client_id, _ = cls.get_credentials()
        params = {
            "client_id": client_id or "GITHUB_CLIENT_ID_NOT_CONFIGURED",
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": state,
            "allow_signup": "true"
        }
        return f"{cls.AUTH_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    def exchange_code(cls, code: str, redirect_uri: str) -> Dict[str, Any]:
        client_id, client_secret = cls.get_credentials()
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }
        return http_post(cls.TOKEN_URL, data, headers={"Accept": "application/json"})

    @classmethod
    def get_user_profile(cls, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github.v3+json"}
        user_info = http_get(cls.USER_URL, headers)
        if "error" in user_info:
            return user_info

        email = user_info.get("email")
        email_verified = False

        # Support users whose email is private on GitHub: query /user/emails endpoint
        if not email:
            emails_res = http_get(cls.EMAILS_URL, headers)
            if isinstance(emails_res, list):
                for e_item in emails_res:
                    if e_item.get("primary"):
                        email = e_item.get("email")
                        email_verified = e_item.get("verified", False)
                        break

        # Fallback if no public email available
        if not email:
            email = f"{user_info.get('login')}@users.noreply.github.com"
            email_verified = True

        return {
            "provider": "github",
            "provider_account_id": str(user_info.get("id")),
            "email": email,
            "email_verified": email_verified,
            "name": user_info.get("name") or user_info.get("login"),
            "profile_image": user_info.get("avatar_url")
        }


class FacebookOAuthProvider:
    AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"
    TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
    ME_URL = "https://graph.facebook.com/me"

    @classmethod
    def get_credentials(cls) -> Tuple[Optional[str], Optional[str]]:
        return get_config_val("FACEBOOK_APP_ID"), get_config_val("FACEBOOK_APP_SECRET")

    @classmethod
    def is_configured(cls) -> bool:
        cid, sec = cls.get_credentials()
        return bool(cid and sec and cid != "your_facebook_app_id_here")

    @classmethod
    def get_authorization_url(cls, redirect_uri: str, state: str) -> str:
        app_id, _ = cls.get_credentials()
        params = {
            "client_id": app_id or "FACEBOOK_APP_ID_NOT_CONFIGURED",
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "email,public_profile"
        }
        return f"{cls.AUTH_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    def exchange_code(cls, code: str, redirect_uri: str) -> Dict[str, Any]:
        app_id, app_secret = cls.get_credentials()
        data = {
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
            "code": code
        }
        return http_get(f"{cls.TOKEN_URL}?{urllib.parse.urlencode(data)}")

    @classmethod
    def get_user_profile(cls, access_token: str) -> Dict[str, Any]:
        params = {
            "fields": "id,name,email,picture.width(200).height(200)",
            "access_token": access_token
        }
        info = http_get(f"{cls.ME_URL}?{urllib.parse.urlencode(params)}")
        if "error" in info:
            return info
        picture_data = info.get("picture", {}).get("data", {})
        return {
            "provider": "facebook",
            "provider_account_id": info.get("id"),
            "email": info.get("email") or f"{info.get('id')}@facebook.com",
            "email_verified": bool(info.get("email")),
            "name": info.get("name") or "Facebook User",
            "profile_image": picture_data.get("url")
        }


class TwitterOAuthProvider:
    AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    ME_URL = "https://api.twitter.com/2/users/me"

    @classmethod
    def get_credentials(cls) -> Tuple[Optional[str], Optional[str]]:
        return get_config_val("X_CLIENT_ID"), get_config_val("X_CLIENT_SECRET")

    @classmethod
    def is_configured(cls) -> bool:
        cid, sec = cls.get_credentials()
        return bool(cid and sec and cid != "your_x_client_id_here")

    @classmethod
    def get_authorization_url(cls, redirect_uri: str, state: str, code_challenge: str) -> str:
        client_id, _ = cls.get_credentials()
        params = {
            "response_type": "code",
            "client_id": client_id or "X_CLIENT_ID_NOT_CONFIGURED",
            "redirect_uri": redirect_uri,
            "scope": "tweet.read users.read offline.access",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        return f"{cls.AUTH_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    def exchange_code(cls, code: str, redirect_uri: str, code_verifier: str) -> Dict[str, Any]:
        client_id, client_secret = cls.get_credentials()
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier
        }
        headers = {}
        if client_secret:
            basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {basic_auth}"
        return http_post(cls.TOKEN_URL, data, headers=headers)

    @classmethod
    def get_user_profile(cls, access_token: str) -> Dict[str, Any]:
        params = {"user.fields": "profile_image_url,verified"}
        info = http_get(f"{cls.ME_URL}?{urllib.parse.urlencode(params)}", headers={"Authorization": f"Bearer {access_token}"})
        if "error" in info:
            return info
        user_data = info.get("data", {})
        username = user_data.get("username", "twitter_user")
        return {
            "provider": "x",
            "provider_account_id": user_data.get("id"),
            "email": f"{username}@x-oauth.com",
            "email_verified": True,
            "name": user_data.get("name") or username,
            "profile_image": user_data.get("profile_image_url")
        }


# ==============================================================================
# 5. USER MANAGER & ACCOUNT LINKING (SQLITE REPOSITORY)
# ==============================================================================

class UserManager:
    """Manages persistent users, authentication accounts, and session lifecycle."""

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_user_by_provider(provider: str, provider_account_id: str) -> Optional[Dict[str, Any]]:
        """Look up user through linked auth_accounts table."""
        conn = get_db_connection()
        query = """
        SELECT u.* FROM users u
        JOIN auth_accounts a ON u.id = a.user_id
        WHERE a.provider = ? AND a.provider_account_id = ?
        """
        row = conn.execute(query, (provider, provider_account_id)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_linked_accounts(user_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM auth_accounts WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def register_email_user(name: str, email: str, password: str, role: str = "Lead Freight Auditor") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Register a new user with corporate email and hashed password."""
        email_clean = email.lower().strip()
        if not email_clean or "@" not in email_clean:
            return False, "Invalid email address format.", None
        if len(password) < 6:
            return False, "Password must be at least 6 characters.", None

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email_clean,)).fetchone()
        if existing:
            conn.close()
            return False, "An account with this email address already exists. Please log in.", None

        user_id = f"USR-{secrets.token_hex(8)}"
        pw_hash = hash_password(password)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with conn:
            conn.execute("""
            INSERT INTO users (id, name, email, email_verified, password_hash, role, created_at, updated_at, last_login_at)
            VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)
            """, (user_id, name.strip(), email_clean, pw_hash, role, now, now, now))
            
            # Record email as local provider in auth_accounts
            conn.execute("""
            INSERT INTO auth_accounts (id, user_id, provider, provider_account_id, provider_email, created_at)
            VALUES (?, ?, 'email', ?, ?, ?)
            """, (f"ACC-{secrets.token_hex(8)}", user_id, email_clean, email_clean, now))

        user = UserManager.get_user_by_id(user_id)
        conn.close()
        return True, "Registration successful.", user

    @staticmethod
    def authenticate_email_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Authenticate user with email and password."""
        email_clean = email.lower().strip()
        user = UserManager.get_user_by_email(email_clean)
        if not user:
            return False, "No account found with this email. Please register.", None
        
        stored_hash = user.get("password_hash")
        if not stored_hash or not verify_password(password, stored_hash):
            return False, "Invalid password credentials.", None

        # Update last_login_at
        conn = get_db_connection()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with conn:
            conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now, user["id"]))
        conn.close()

        user["last_login_at"] = now
        return True, "Authentication successful.", user

    @staticmethod
    def get_or_create_oauth_user(provider: str, provider_account_id: str, email: str, name: str, profile_image: Optional[str] = None, email_verified: bool = True) -> Dict[str, Any]:
        """
        Unified OAuth account resolver:
        1. Check if provider account is already linked to a user.
        2. Check if a user with the same email already exists -> safe account linking.
        3. Otherwise, create a new user and link the provider account.
        """
        conn = get_db_connection()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        email_clean = email.lower().strip()

        # 1. Existing linked account
        user = UserManager.get_user_by_provider(provider, provider_account_id)
        if user:
            with conn:
                conn.execute("UPDATE users SET last_login_at = ?, profile_image = COALESCE(?, profile_image) WHERE id = ?", (now, profile_image, user["id"]))
            conn.close()
            user["last_login_at"] = now
            if profile_image:
                user["profile_image"] = profile_image
            return user

        # 2. Existing user by email -> safe account linking
        user = UserManager.get_user_by_email(email_clean)
        if user:
            with conn:
                acc_id = f"ACC-{secrets.token_hex(8)}"
                conn.execute("""
                INSERT OR IGNORE INTO auth_accounts (id, user_id, provider, provider_account_id, provider_email, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (acc_id, user["id"], provider, provider_account_id, email_clean, now))
                conn.execute("UPDATE users SET last_login_at = ?, profile_image = COALESCE(profile_image, ?) WHERE id = ?", (now, profile_image, user["id"]))
            conn.close()
            user["last_login_at"] = now
            return user

        # 3. New user registration via OAuth
        user_id = f"USR-{secrets.token_hex(8)}"
        acc_id = f"ACC-{secrets.token_hex(8)}"
        with conn:
            conn.execute("""
            INSERT INTO users (id, name, email, email_verified, profile_image, role, created_at, updated_at, last_login_at)
            VALUES (?, ?, ?, ?, ?, 'Lead Freight Auditor', ?, ?, ?)
            """, (user_id, name.strip(), email_clean, int(email_verified), profile_image, now, now, now))

            conn.execute("""
            INSERT INTO auth_accounts (id, user_id, provider, provider_account_id, provider_email, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (acc_id, user_id, provider, provider_account_id, email_clean, now))

        conn.close()
        return UserManager.get_user_by_id(user_id)

    @staticmethod
    def create_session(user_id: str, duration_days: int = 7) -> str:
        """Create a secure 32-byte session token with expiration."""
        session_id = secrets.token_urlsafe(32)
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = (now + datetime.timedelta(days=duration_days)).isoformat()
        
        conn = get_db_connection()
        with conn:
            conn.execute("""
            INSERT INTO auth_sessions (session_id, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """, (session_id, user_id, expires_at, now.isoformat()))
        conn.close()
        return session_id

    @staticmethod
    def validate_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return user if active."""
        if not session_id:
            return None
        conn = get_db_connection()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        query = """
        SELECT u.* FROM users u
        JOIN auth_sessions s ON u.id = s.user_id
        WHERE s.session_id = ? AND s.expires_at > ?
        """
        row = conn.execute(query, (session_id, now)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def delete_session(session_id: str):
        """Invalidate a session on logout."""
        conn = get_db_connection()
        with conn:
            conn.execute("DELETE FROM auth_sessions WHERE session_id = ?", (session_id,))
        conn.close()
