"""
Unit and Integration Tests for Production Auth Engine & OAuth Providers.
"""
import pytest
import hashlib
import base64
from src.auth import (
    hash_password, verify_password, generate_csrf_state, generate_pkce_pair,
    UserManager, GoogleOAuthProvider, GitHubOAuthProvider, FacebookOAuthProvider, TwitterOAuthProvider
)

def test_password_hashing():
    """Verify cryptographically secure salted password hashing."""
    pw = "SuperSecureFreightPassword@2026"
    stored_hash = hash_password(pw)
    assert stored_hash != pw
    assert "$" in stored_hash
    assert verify_password(pw, stored_hash) is True
    assert verify_password("WrongPassword@123", stored_hash) is False

def test_pkce_generation():
    """Verify PKCE code_verifier and S256 code_challenge standard compliance."""
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) >= 43
    assert len(challenge) >= 43
    
    # Recalculate manually to verify S256 RFC-7636 compliance
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    expected_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    assert challenge == expected_challenge

def test_csrf_state_generation():
    """Verify CSRF state token generation entropy."""
    s1 = generate_csrf_state()
    s2 = generate_csrf_state()
    assert len(s1) >= 32
    assert s1 != s2

def test_user_email_registration_and_auth():
    """Verify user registration, duplicate prevention, and authentication."""
    test_email = "test.auditor@logistics-test.com"
    success, msg, user = UserManager.register_email_user("Test Auditor", test_email, "FreightPass2026!", "Senior Auditor")
    
    # If already registered in a previous test run, get the user
    if not success:
        user = UserManager.get_user_by_email(test_email)
        assert user is not None
    else:
        assert success is True
        assert user["email"] == test_email
        assert user["name"] == "Test Auditor"

    # Verify authentication success
    ok, auth_msg, auth_user = UserManager.authenticate_email_user(test_email, "FreightPass2026!")
    assert ok is True
    assert auth_user["id"] == user["id"]

    # Verify wrong password failure
    fail, fail_msg, _ = UserManager.authenticate_email_user(test_email, "WrongPassword!")
    assert fail is False
    assert "Invalid" in fail_msg

def test_oauth_user_creation_and_account_linking():
    """Verify OAuth user creation and multiple provider linking to one email."""
    oauth_email = "unified.shipper@global-tms.com"
    
    # 1. Sign in first time via Google
    u1 = UserManager.get_or_create_oauth_user(
        provider="google",
        provider_account_id="google-sub-987654",
        email=oauth_email,
        name="Unified Shipper",
        profile_image="https://lh3.googleusercontent.com/test-pic.jpg"
    )
    assert u1 is not None
    assert u1["email"] == oauth_email

    # 2. Sign in same user later via GitHub with same email -> links safely!
    u2 = UserManager.get_or_create_oauth_user(
        provider="github",
        provider_account_id="github-id-12345",
        email=oauth_email,
        name="Unified Shipper",
        profile_image="https://avatars.githubusercontent.com/u/test"
    )
    assert u2["id"] == u1["id"]

    # Verify both accounts linked
    linked = UserManager.get_linked_accounts(u1["id"])
    providers = [acc["provider"] for acc in linked]
    assert "google" in providers
    assert "github" in providers

def test_session_lifecycle():
    """Verify session creation, validation, and logout deletion."""
    user = UserManager.get_or_create_oauth_user("test", "test-123", "session.test@domain.com", "Session User")
    session_id = UserManager.create_session(user["id"])
    assert session_id is not None
    
    # Validate session
    active_user = UserManager.validate_session(session_id)
    assert active_user is not None
    assert active_user["id"] == user["id"]

    # Delete session (Logout)
    UserManager.delete_session(session_id)
    logged_out_user = UserManager.validate_session(session_id)
    assert logged_out_user is None

def test_oauth_authorization_urls():
    """Verify authorization URL formatting across all 4 providers."""
    redirect_uri = "https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app"
    state = "test_csrf_state"
    
    # Google (must have prompt=select_account)
    g_url = GoogleOAuthProvider.get_authorization_url(redirect_uri, state)
    assert "accounts.google.com" in g_url
    assert "prompt=select_account" in g_url
    assert "scope=openid+email+profile" in g_url or "scope=openid%20email%20profile" in g_url

    # GitHub
    gh_url = GitHubOAuthProvider.get_authorization_url(redirect_uri, state)
    assert "github.com/login/oauth/authorize" in gh_url
    assert "read%3Auser" in gh_url or "read:user" in gh_url

    # Facebook
    fb_url = FacebookOAuthProvider.get_authorization_url(redirect_uri, state)
    assert "facebook.com" in fb_url
    assert "email%2Cpublic_profile" in fb_url or "email,public_profile" in fb_url

    # X / Twitter (must have code_challenge and S256)
    v, challenge = generate_pkce_pair()
    x_url = TwitterOAuthProvider.get_authorization_url(redirect_uri, state, challenge)
    assert "twitter.com/i/oauth2/authorize" in x_url
    assert "code_challenge_method=S256" in x_url
    assert f"code_challenge={challenge}" in x_url
