# Enterprise OAuth 2.0 & Production Authentication Setup Guide

This guide provides complete instructions for registering credentials and enabling real OAuth 2.0 / OpenID Connect authentication across Google, GitHub, Facebook, and X (Twitter) in **FreightGuard AI**.

---

## 1. Architecture Overview

FreightGuard AI implements production-grade authentication with:
- **Zero Account Leakage:** Authentications run via genuine OAuth 2.0 protocols directly on the provider's domain. Each visitor sees their *own* accounts logged into their browser.
- **Provider Multi-Tenancy:** A unified SQLite database (`data/freight_audit.db`) stores user profiles (`users`), provider credentials (`auth_accounts`), and session tokens (`auth_sessions`).
- **Cryptographic Security:** Passwords hashed with PBKDF2-HMAC-SHA256 (100,000 rounds, 16-byte cryptographically secure salt). CSRF state tokens and PKCE S256 code challenge for X (Twitter).
- **Dual Runtime Support:** Operates seamlessly on both the Streamlit UI control tower and FastAPI enterprise REST API (`/auth/status`, `/auth/{provider}/login`, `/auth/{provider}/callback`, etc.).

---

## 2. Callback & Redirect URIs

When creating OAuth credentials in each provider's developer console, register the following URLs:

### Production (Streamlit Cloud Application)
```text
https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app
```

### Local Development (Streamlit UI)
```text
http://localhost:8501
```

### REST API Endpoints (FastAPI Backend)
```text
http://127.0.0.1:8000/auth/google/callback
http://127.0.0.1:8000/auth/github/callback
http://127.0.0.1:8000/auth/facebook/callback
http://127.0.0.1:8000/auth/x/callback
```

---

## 3. Step-by-Step Developer Portal Setup

### 🔴 A. Google Sign-In (OpenID Connect with Account Chooser)

1. Navigate to [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials).
2. Click **Create Project** (or select your existing project).
3. In **OAuth consent screen**:
   - Select **External**.
   - Fill in App Name: `FreightGuard AI`.
   - Add scopes: `openid`, `https://www.googleapis.com/auth/userinfo.email`, `https://www.googleapis.com/auth/userinfo.profile`.
4. In **Credentials** -> **Create Credentials** -> **OAuth Client ID**:
   - Application type: **Web application**.
   - Authorized JavaScript origins:
     - `https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app`
     - `http://localhost:8501`
   - Authorized redirect URIs:
     - `https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app`
     - `http://127.0.0.1:8000/auth/google/callback`
5. Copy your **Client ID** and **Client Secret**.
6. Set in `.env`:
   ```env
   GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```
> **Note on Account Chooser:** FreightGuard AI requests authorization with `prompt=select_account`. This forces Google to display the "Choose an account" dialog on Google's own domain for all active accounts in the visitor's browser.

---

### 🐙 B. GitHub Sign-In

1. Navigate to [GitHub Developer Settings](https://github.com/settings/developers).
2. Click **New OAuth App**.
3. Fill in the fields:
   - Application name: `FreightGuard AI Enterprise`
   - Homepage URL: `https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app`
   - Authorization callback URL: `https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app`
4. Click **Register application**.
5. Click **Generate a new client secret**.
6. Set in `.env`:
   ```env
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   ```
> **Note on Private Emails:** If a user configures their GitHub email as private, FreightGuard AI queries `https://api.github.com/user/emails` using their bearer token to retrieve their verified primary email address.

---

### 🔵 C. Meta Facebook Login

1. Navigate to [Meta for Developers](https://developers.facebook.com/apps).
2. Click **Create App** -> Select **Authenticate and request data from users with Facebook Login**.
3. Under **Facebook Login** -> **Settings**:
   - Valid OAuth Redirect URIs:
     - `https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app`
     - `http://127.0.0.1:8000/auth/facebook/callback`
4. Under **App Settings** -> **Basic**, copy **App ID** and **App Secret**.
5. Set in `.env`:
   ```env
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   ```

---

### 𝕏 D. X (Twitter) OAuth 2.0 with PKCE

1. Navigate to [X Developer Portal Dashboard](https://developer.twitter.com/en/portal/dashboard).
2. Create or select a Project and App.
3. Under **User authentication settings**, click **Set up**:
   - App permissions: **Read**.
   - Type of App: **Web App**.
   - Callback URI / Redirect URL:
     - `https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app`
     - `http://127.0.0.1:8000/auth/x/callback`
   - Website URL: `https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app`
4. Save and copy **OAuth 2.0 Client ID** and **Client Secret**.
5. Set in `.env`:
   ```env
   X_CLIENT_ID=your_x_client_id
   X_CLIENT_SECRET=your_x_client_secret
   ```
> **Note on PKCE:** FreightGuard AI automatically generates a cryptographically random 64-byte `code_verifier` and its SHA256 base64url-encoded `code_challenge` per standard RFC 7636.

---

## 4. Configuring Streamlit Cloud Secrets

When hosting on Streamlit Cloud:
1. Open your app dashboard at [share.streamlit.io](https://share.streamlit.io).
2. Select your app `luffy-2601-yottaflex-ai-app-rvlcha`.
3. Click **Settings** (⚙️) -> **Secrets**.
4. Paste your credentials:
```toml
APP_URL = "https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app"
GOOGLE_CLIENT_ID = "..."
GOOGLE_CLIENT_SECRET = "..."
GITHUB_CLIENT_ID = "..."
GITHUB_CLIENT_SECRET = "..."
FACEBOOK_APP_ID = "..."
FACEBOOK_APP_SECRET = "..."
X_CLIENT_ID = "..."
X_CLIENT_SECRET = "..."
```
5. Click **Save**. Streamlit Cloud will automatically restart the app with the new credentials.

---

## 5. GitHub Pages 404 Notice

If you visit `https://luffy-2601.github.io/Yottaflex-AI/` and see `404 There isn't a GitHub Pages site here`:
- **Why it happened:** GitHub Pages hosts static web pages, while your Python Streamlit application runs live on Streamlit Cloud at `https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app/`.
- **Solution:** We added an automatic `index.html` redirect at the root of the repository. If you choose to enable GitHub Pages in your repository under **Settings** -> **Pages** -> Source: **Deploy from a branch (main)**, visiting `https://luffy-2601.github.io/Yottaflex-AI/` will now immediately redirect visitors to your live Streamlit Cloud application!
