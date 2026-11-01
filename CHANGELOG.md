# Changelog

All notable changes to **FreightGuard AI** are documented in this file.

---

## [2.0.0] - 2026-11-01

### Added
- **Production Social OAuth 2.0 Engine:** Official integrations for Google Sign-In (with `prompt=select_account`), GitHub OAuth, Meta Facebook Login, and X / Twitter OAuth 2.0 with PKCE S256.
- **SQLite Authentication Persistence:** Integrated `users`, `auth_accounts`, and `auth_sessions` tables in `data/freight_audit.db` with foreign key integrity.
- **Cryptographic Security:** Salted PBKDF2-HMAC-SHA256 password hashing and CSRF state token generation.
- **FastAPI Authentication Endpoints:** Added `/auth/status`, `/auth/{provider}/login`, `/auth/{provider}/callback`, `/auth/register`, `/auth/login`, `/auth/me`, and `/auth/logout`.
- **Automated Test Suite Expansion:** 32 comprehensive tests across core audit engine, analytics, API, and authentication.
- **Developer Setup Documentation:** Added [`docs/OAUTH_SETUP_GUIDE.md`](docs/OAUTH_SETUP_GUIDE.md) and [`.env.example`](.env.example).

### Changed
- Refactored `app.py` authentication gate to cleanly handle OAuth query parameters (`?code=...&state=...`) and display user avatars in the sidebar.
- Completely removed all static/mock account arrays to guarantee zero credential leakage between concurrent visitors.

---

## [1.5.0] - 2026-10-31

### Added
- **Palantir-Style Executive Web Control Tower:** Built dynamic interactive Streamlit application with Cyber Dark and Executive Light themes.
- **What-If Supply Chain Simulator:** Dynamic sensitivity analysis for diesel fuel surcharges and packaging dimensional adjustments.
- **Carrier Billing Integrity Scorecard (CBIS):** Automated carrier risk ranking (Tier 1 Trusted vs Tier 3 High-Risk Audit Hold).
- **1-Click Legal Dispute Memo Generator:** Automated formal dispute letters with legal citation and audit trail.
- **Interactive Offline HTML Report:** Created standalone single-file audit report in `index.html` with real-time JavaScript filtering.

---

## [1.0.0] - 2026-10-30

### Added
- **Core 4-Gate Freight Audit Engine:** Zero-dependency Python engine auditing 15,000 invoices in under 7 seconds.
- **Detection of 6 Billing Tricks:** Phantom shipments, expired tariffs, weight bracket mismatches, duplicate surcharges, excessive credit notes, and unauthorized accessorials.
- **Synthetic Data Generator:** Seed-based deterministic freight data generator (`--scale starter` and `--scale full`).
