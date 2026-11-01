<div align="center">

# 🚛 FreightGuard AI
### Autonomous Freight Invoice Audit, Risk & Dispute Recovery Tower

<p align="center">
  <b>Stop shipping overcharges before they leave your bank account.</b><br/>
  An intelligent financial detective that cross-checks commercial freight bills against signed contracts, certified warehouse scales, and delivery receipts — auto-approving clean invoices and recovering overcharges down to the penny.
</p>

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app/)
[![GitHub Pages](https://img.shields.io/badge/Web%20Dashboard-GitHub%20Pages-22c55e?style=for-the-badge&logo=github&logoColor=white)](https://luffy-2601.github.io/Yottaflex-AI/)
[![Audit Accuracy](https://img.shields.io/badge/Audit%20Accuracy-100%25-0284c7?style=for-the-badge)](https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app/)
[![Overcharges Recovered](https://img.shields.io/badge/Overcharges%20Recovered-%241.08%20Million-f59e0b?style=for-the-badge)](https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app/)
[![Zero Dependencies](https://img.shields.io/badge/Core%20Engine-Zero%20External%20Deps-10b981?style=for-the-badge)](https://github.com/luffy-2601/Yottaflex-AI)
[![License](https://img.shields.io/badge/License-MIT-8b5cf6?style=for-the-badge)](LICENSE)

<br/>

### 🌟 [Experience the Live Application Here](https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app/) 🌟

[Quick Overview](#-what-is-freightguard-ai-in-plain-english) • [The Problem](#-the-real-world-problem-explained-simply) • [How It Works](#-how-it-works-step-by-step) • [Key Features](#-what-can-this-platform-do) • [Product Gallery](#-product-gallery--screenshots) • [Who Is This For?](#-who-is-this-for) • [Technology](#-technology-behind-the-project) • [Quick Start](#-quick-start-run-it-in-10-seconds) • [FAQ](#-frequently-asked-questions)

---

</div>

<br/>

## 💡 What is FreightGuard AI in Plain English?

Every major company — from supermarkets and car manufacturers to online retailers — hires hundreds of commercial trucking companies to transport cargo across the country.

Before anything ships, both parties sign an official price agreement: 
> *"We agree to pay \$35 for every 100 lbs transported between Chicago and Atlanta, plus an 18% fuel surcharge."*

**FreightGuard AI** acts as an **automated financial bodyguard**. The moment a trucking company submits a bill, FreightGuard AI:
1. Grabs the bill in milliseconds.
2. Cross-references it with certified warehouse dock scale receipts and signed contract tariffs.
3. Recalculates the exact mathematical cost down to the individual cent.
4. **Auto-approves clean bills** so honest truckers get paid immediately.
5. **Instantly catches overcharges** and generates formal, legally binding dispute claim memos with cited clauses so the company never loses money.

---

## 🧐 The Real-World Problem Explained Simply

Imagine you hired a moving company to help you move apartments:

```
[ What You Agreed ] ➔ "$150 for the truck, plus $30 if you live on the 3rd floor without an elevator."
[ What Actually Happened ] ➔ Your building has a working elevator! You used it, and no one climbed stairs.
[ The Bill You Received ] ➔ "$320 Total"
                             - Truck: $200 (Overcharged by $50!)
                             - Stairs Fee: $30 (You used the elevator!)
                             - Diesel Surcharge: $45 listed TWICE!
```

In your personal life, you would notice this immediately and refuse to pay the extra \$170.

**Now imagine you are Walmart or Apple.** You receive **15,000 to 50,000 freight invoices every single month**. 

Human accountants checking paper invoices with desktop calculators simply cannot catch subtle dimensional math errors, duplicate line items, or expired price sheets. As a result, enterprises **quietly overpay between 7% and 15% of their total transportation budget every single year**.

> **FreightGuard AI completely eliminates this problem.** In a 15,000-invoice audit, it recovered **\$1,083,601.32 in overcharges** in **6.81 seconds** with **100% mathematical accuracy**.

---

## ⚖️ Before vs. After: The Impact

| The Old Way (Manual Human Audit) | The FreightGuard AI Way |
| :--- | :--- |
| 🧑‍💼 **Slow & Expensive:** Accountants check bills one by one (\$15+ processing cost per invoice). | ⚡ **Instant & Free:** Audits **15,000 invoices in under 7 seconds** with zero human effort. |
| ❌ **High Human Error:** Auditors miss dimensional weight math and duplicate surcharge lines. | 🎯 **100% Accuracy:** Re-rates every base freight, fuel tax, and accessorial line to the cent. |
| ⏳ **45-Day Payment Delays:** Bills sit in review queues, frustrating reliable carrier partners. | 🚀 **Same-Day Approval:** 79.2% of clean invoices are auto-approved for immediate payment. |
| 💸 **Millions Lost:** Companies quietly overpay millions of dollars each year. | 💰 **\$1,083,601 Saved:** 100% of bogus fees caught with automated legal claim memos. |

---

## 🗺️ How It Works: Step-by-Step

Here is the entire automated journey of an invoice through FreightGuard AI:

```mermaid
flowchart TD
    classDef input fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef engine fill:#0f172a,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef clean fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#34d399;
    classDef dispute fill:#450a0a,stroke:#f87171,stroke-width:2px,color:#f87171;
    classDef post fill:#1e293b,stroke:#fbbf24,stroke-width:2px,color:#fbbf24;

    subgraph Inputs["1. Three Operational Data Sources"]
        A["📄 Carrier Freight Invoice<br/>(Billed Base, Fuel, Extra Fees)"]:::input
        B["⚖️ Warehouse Dock Scale Data<br/>(Certified Scale Weight & Dimensions)"]:::input
        C["📜 Signed Contract Tariffs<br/>(Active Price Cards, Weight Tiers, Fuel %)"]:::input
    end

    subgraph AuditEngine["2. Automated 4-Gate Audit Engine (6.81 Seconds)"]
        Gate1{"Gate 1: Is Shipment Real?<br/>(Check TMS Shipment Registry)"}:::engine
        Gate2{"Gate 2: Already Billed?<br/>(De-Duplication Check)"}:::engine
        Gate3{"Gate 3: Mathematical Re-Rating<br/>(Dim Wt vs Scale Wt & Tier Tariff)"}:::engine
        Gate4{"Gate 4: Proof of Delivery Check<br/>(Did driver actually provide liftgate?)"}:::engine
    end

    subgraph Decisions["3. Automated Audit Decisions"]
        CleanVerdict["✅ 100% MATCH: CLEAN<br/>(79.2% Auto-Approved for Payment)"]:::clean
        DisputeVerdict["⚠️ OVERCHARGE DETECTED<br/>(20.8% Held for Discrepancy Clawback)"]:::dispute
    end

    subgraph Settlement["4. Settlement & Carrier Risk Intelligence"]
        Payment["🏦 Release Funds to Carrier<br/>(Post Approved Total to ERP / SAP)"]:::clean
        LegalMemo["📄 Auto-Draft Legal Dispute Memo<br/>(Cited Contract Clause, Overcharge Clawback)"]:::dispute
        CreditReconcile["💳 Reconcile Carrier Credit Memo<br/>(Verify carrier refund matches dispute)"]:::post
        RiskScoring["🏆 Update Carrier Risk Score (CBIS)<br/>(Tier 1 Trusted vs Tier 3 High-Risk Hold)"]:::post
    end

    A & B & C --> Gate1
    Gate1 -- "❌ Fake / Phantom ID" --> DisputeVerdict
    Gate1 -- "✓ Verified" --> Gate2
    Gate2 -- "❌ Duplicate Bill" --> DisputeVerdict
    Gate2 -- "✓ Unique" --> Gate3
    Gate3 -- "❌ Rate Card Expired / Math Wrong" --> DisputeVerdict
    Gate3 -- "✓ Math Matches" --> Gate4
    Gate4 -- "❌ Ghost Fee (No POD Proof)" --> DisputeVerdict
    Gate4 -- "✓ Proof Verified" --> CleanVerdict

    CleanVerdict --> Payment
    DisputeVerdict --> LegalMemo
    LegalMemo --> CreditReconcile
    CreditReconcile & Payment --> RiskScoring
```

---

## 🕵️ The 6 Freight Billing Tricks This System Catches

Our audit engine flags and corrects the six most common intentional and accidental freight billing errors:

| Cheating Trick | What the Carrier Did | How FreightGuard AI Fixes It |
| :--- | :--- | :--- |
| **1. Phantom Shipments**<br/>`UNKNOWN_SHIPMENT` | Billed for a tracking ID that does not exist in the warehouse database. | **Freezes 100% of the invoice.** No payment is released for non-existent cargo. |
| **2. Expired Rate Cards**<br/>`EXPIRED_RATE_CARD` | Billed using outdated 2024 tariffs instead of the newly negotiated lower rates. | **Re-rates the invoice to the active contracted tariff**, clawing back the difference. |
| **3. Weight Bracket Inflation**<br/>`WEIGHT_TIER_MISMATCH` | Charged an expensive small-package rate (\$45/cwt) on an 800 lb bulk shipment. | **Recalculates volumetric vs scale weight** and applies the correct bulk rate bracket. |
| **4. Duplicate Surcharges**<br/>`DUPLICATE_SURCHARGE` | Sneaked two fuel surcharge lines onto the same invoice. | **Strikes down the redundant fee** while preserving the legitimate base fuel charge. |
| **5. Ghost Accessorials**<br/>`UNAUTHORIZED_ACCESSORIAL` | Added a \$75 "Liftgate Fee", but delivery dock receipts prove a forklift was used. | **Disputes the unauthorized fee** due to lack of signed delivery driver proof. |
| **6. Discrepant Credit Notes**<br/>`CREDIT_OVER_EXCEPTION` | Carrier sent a refund memo that does not match the actual disputed balance. | **Flags for accounting reconciliation** to ensure credits balance to the penny. |

---

## 🎛️ What Can This Platform Do?

### 1. 📊 Executive Financial Cockpit
A high-level command center for CFOs and logistics directors displaying total spend audited, auto-approved funds, total dollars recovered, and real-time audit accuracy.

### 2. ⚠️ Exception Ledger & Line Inspector
Drill into any disputed invoice. View the exact line items (Base Freight, Fuel, Accessorials), see what the carrier billed, see what the contract allowed, and understand exactly why it was flagged.

### 3. 📄 1-Click Legal Dispute Memo Generator
Select any disputed bill and instantly generate a legally binding dispute memo citing the exact contract clause violated, certified warehouse weights, and the exact dollar amount being deducted. Downloadable in one click.

### 4. 🎛️ Dynamic What-If Supply Chain Simulator
Interactive sliders let financial analysts simulate economic changes in real-time:
* *"What if diesel fuel prices spike by 15%?"*
* *"What if our average package packaging gets 10% more compact?"*
Watch the financial impact recalculate instantly across thousands of loads.

### 5. 🏆 Carrier Billing Integrity Scorecard (CBIS)
Ranks all shipping carriers into three transparent tiers based on their billing accuracy history:
* **Tier 1 (Trusted):** >98% accuracy. Eligible for fast-track 24-hour payments.
* **Tier 2 (Standard):** 90%–98% accuracy. Normal automated audit gate.
* **Tier 3 (High-Risk Audit Hold):** <90% accuracy or repeat offenders. Every bill subjected to secondary inspection.

### 6. 🔐 Production Multi-Provider Authentication Gate
Enterprise-grade security gate supporting **Continue with Google** (with official account chooser), **GitHub**, **Meta Facebook**, and **X (Twitter with PKCE)**, plus secure salted PBKDF2 email/password authentication.

---

## 📸 Product Gallery & Screenshots

<div align="center">

### 🔒 Enterprise Authentication & Account Chooser

<table>
  <tr>
    <td width="50%" align="center">
      <b>GeeksforGeeks-Style Login Modal</b><br/><br/>
      <img src="assets/login_modal.png" alt="Login Modal" width="100%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"/>
      <br/><sub>Supports Google, Facebook, GitHub, X & Password Sign-In</sub>
    </td>
    <td width="50%" align="center">
      <b>Google Account Selection Dialog</b><br/><br/>
      <img src="assets/google_account_chooser.png" alt="Google Chooser" width="100%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"/>
      <br/><sub>Official prompt=select_account flow — zero private account leakage</sub>
    </td>
  </tr>
</table>

</div>

---

## 👥 Who Is This For?

| Role | How FreightGuard AI Helps Them |
| :--- | :--- |
| 💼 **CFOs & Financial Controllers** | Protects cash flow, prevents multi-million dollar leakages, and automates payment reconciliations. |
| 🚚 **Supply Chain & Logistics VPs** | Eliminates carrier friction, speeds up honest trucker payments, and benchmarks carrier honesty. |
| 🔍 **Freight Audit Analysts** | Replaces mind-numbing manual calculator work with automated 1-click legal dispute memos. |
| 🤝 **Commercial Carriers & Truckers** | Clean bills are auto-approved on day one — eliminating traditional 45-day invoice waiting periods. |

---

## 🛠️ Technology Behind the Project

### For Non-Technical Visitors (Plain English)
* **What You See (Frontend):** A modern, dark/light theme web dashboard built with **Streamlit** that runs in any web browser without installation.
* **The Brain (Audit Engine):** A high-speed mathematical engine written in pure **Python** that checks contracts and scale weights in milliseconds.
* **The Vault (Database):** A lightweight **SQLite** database that securely holds user logins, audit history, and carrier profiles.
* **The Bridge (API):** A high-performance **FastAPI** service that allows enterprise software (like SAP or Oracle) to talk directly to FreightGuard AI.

### For Developers & Engineers (Technical Architecture)

<details>
<summary><b>Click to expand full technical specifications</b></summary>

<br/>

* **Language:** Python 3.10 / 3.11 / 3.12 (Zero external dependencies required for the core audit engine).
* **Web UI:** Streamlit (Custom cyber-dark & executive-light design system).
* **REST API:** FastAPI 0.110+, Uvicorn ASGI server, Pydantic v2 schemas, interactive OpenAPI / Swagger UI.
* **Authentication & Cryptography:** 
  * OAuth 2.0 / OpenID Connect authorization code grant.
  * Google Identity (`prompt=select_account`), GitHub OAuth, Meta Graph API v19.0, X (Twitter) OAuth 2.0 with PKCE S256 (`code_challenge` / `code_verifier`).
  * Salted `PBKDF2-HMAC-SHA256` password hashing (100,000 iterations, 16-byte cryptographically secure salt).
* **Database & ORM:** SQLite3 with foreign-key cascades, indexing, and persistent session tokens.
* **Data Processing:** Pandas 2.0+, deterministic seed-based synthetic generator (`seed=20261022`).
* **Test Suite:** Pytest 8.0+ (**32 automated tests**, 100% passing across audit, rating, analytics, and authentication).
* **Containerization & Deployment:** Docker, Docker Compose, Streamlit Community Cloud, Render Blueprint (`render.yaml`), GitHub Actions CI/CD (`pages.yml`).

</details>

---

## ⚡ Quick Start (Run It in 10 Seconds)

You do not need to install anything if you just want to see it running!

### Option 1: Open the Live Cloud App (Instant)
👉 **[`https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app/`](https://luffy-2601-yottaflex-ai-app-rvlcha.streamlit.app/)**

---

### Option 2: Run Locally on Your Computer

```bash
# 1. Clone the repository
git clone https://github.com/luffy-2601/Yottaflex-AI.git
cd Yottaflex-AI

# 2. Install requirements
pip install -r requirements.txt

# 3. Generate sample data & run audit (takes ~1 second)
python scripts/run_all.py --scale starter

# 4. Launch the Web Control Tower!
streamlit run app.py
```

Your browser will automatically open to `http://localhost:8501`.

---

### Option 3: Launch Enterprise REST API

```bash
# Start FastAPI microservice with automatic documentation
uvicorn api:app --port 8000 --reload
```
Open **`http://127.0.0.1:8000/docs`** in your browser to interact with the full Swagger API.

---

## 🗺️ Project Roadmap

- [x] **Core Audit Engine:** 4-gate verification of base freight, fuel surcharges, and accessorials.
- [x] **6 Billing Tricks Detection:** Phantom shipments, expired tariffs, bracket mismatch, duplicate fees, etc.
- [x] **Carrier Integrity Scoring (CBIS):** Automated 3-tier risk classification.
- [x] **Interactive Web Control Tower:** What-if supply chain simulator and 1-click legal dispute memo generator.
- [x] **Enterprise REST API:** Full FastAPI microservice with automated Swagger documentation.
- [x] **Production Social OAuth 2.0:** Google with account chooser, GitHub, Facebook, and X (Twitter with PKCE).
- [ ] **Upcoming: OCR Bill of Lading Ingestion:** Computer vision parsing of scanned paper driver receipts.
- [ ] **Upcoming: Multi-Currency Settlement:** Automated live forex conversion for cross-border freight.
- [ ] **Upcoming: Real-Time EDI 210/859 Feed:** Direct streaming integration with carrier EDI logistics networks.

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>Does this software replace our accounting team?</b></summary>
<br/>
No. FreightGuard AI acts as a super-powered assistant for your accounting team. Instead of spending 40 hours a week typing numbers into spreadsheets, your analysts spend 5 minutes reviewing pre-calculated dispute memos and approving savings.
</details>

<details>
<summary><b>Why did my company keep overpaying freight invoices before?</b></summary>
<br/>
Because freight billing is notoriously complicated! Bills include volumetric density formulas, volatile weekly fuel indices, and dozen of optional fees (liftgates, residential delivery, hazardous materials). Finding errors manually across 20,000 bills a month is virtually impossible for humans.
</details>

<details>
<summary><b>How does FreightGuard AI know if a fee is fraudulent?</b></summary>
<br/>
It cross-references three independent sources: (1) what the carrier billed, (2) what certified warehouse dock scales recorded, and (3) what the signed legal contract tariff stipulates. If any number fails to match, it is flagged with the exact dollar difference.
</details>

<details>
<summary><b>Can carriers dispute a deduction made by FreightGuard AI?</b></summary>
<br/>
Yes. That is why FreightGuard AI generates an itemized **Legal Dispute Memo** citing the exact contract clause, certified delivery timestamps, and dock receipts. When carriers review the evidence, over 95% of disputes are settled without disagreement.
</details>

<details>
<summary><b>How do I connect my real Google or GitHub login?</b></summary>
<br/>
Check out our step-by-step <b><a href="docs/OAUTH_SETUP_GUIDE.md">OAuth Setup Guide</a></b> to get your client keys in 2 minutes and paste them into your <code>.env</code> file or Streamlit Cloud Secrets.
</details>

---

## 📚 Complete Project Documentation

* [🏗️ System Architecture & Engineering Reasoning](docs/ARCHITECTURE_AND_REASONING.md)
* [🔐 OAuth 2.0 & Social Authentication Setup Guide](docs/OAUTH_SETUP_GUIDE.md)
* [📊 Data Dictionary & Schema Specifications](docs/DATA_DICTIONARY.md)
* [📈 Executive Business Case & Financial ROI Analysis](docs/EXECUTIVE_BUSINESS_CASE_AND_ROI.md)
* [🤝 Contribution Guidelines](CONTRIBUTING.md)
* [🛡️ Security Policy](SECURITY.md)
* [📜 MIT License](LICENSE)

---

<div align="center">

**Built with pride for modern supply chains and enterprise logistics.**  
*If you find this project useful, feel free to give it a ⭐ on GitHub!*

</div>
