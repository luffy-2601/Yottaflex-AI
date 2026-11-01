# Security Policy

FreightGuard AI takes the security of financial data, corporate supply chain records, and authentication credentials seriously.

---

## 🔒 Supported Versions

| Version | Supported |
| :--- | :--- |
| 2.0.x (Current - OAuth 2.0 & Cloud Control Tower) | :white_check_mark: |
| 1.x (CLI & Legacy Audit Engine) | :white_check_mark: |

---

## 🛡️ Security Architecture & Best Practices

1. **No Hardcoded Secrets:** Client IDs, secrets, and database credentials must never be committed to Git. All secrets are managed via `.env` or Streamlit Cloud Secrets.
2. **PBKDF2 Password Hashing:** User passwords are encrypted using `hashlib.pbkdf2_hmac` with `SHA-256`, 100,000 iterations, and a unique 16-byte cryptographically secure salt.
3. **OAuth 2.0 & PKCE:** All external authorizations enforce CSRF state tokens, OpenID Connect token verification, and PKCE S256 code challenge/verifier pairs for public clients.
4. **Zero Account Leakage:** Browser sessions are strictly isolated. Authentications run on official provider domains (`accounts.google.com`, `github.com/login/oauth`), ensuring no visitor credentials or accounts are visible to other users.

---

## 🚨 Reporting a Vulnerability

If you discover a potential security vulnerability, please do NOT create a public GitHub issue. 

Instead, report it directly by emailing the maintainers or creating a private vulnerability report on GitHub under **Security** ➔ **Advisories**.

We aim to acknowledge reports within 24 hours and provide an estimated timeline for remediation.
