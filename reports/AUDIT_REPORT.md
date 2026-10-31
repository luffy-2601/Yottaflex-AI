# Freight Invoice Audit & Dispute Reconciliation Report

**Generated:** 2026-10-31 14:25:15 UTC  
**Deterministic Seed:** `20261022`  
**Dataset Scale:** `FULL`  

---

## 1. Executive Summary & KPIs

| Metric | Value | Business Interpretation |
| :--- | :--- | :--- |
| **Total Invoices Audited** | **15,000** | 100% of carrier billing throughput evaluated. |
| **Clean Invoices (Auto-Approved)** | **11,874** (79.2%) | Invoices matching contracted rates & verified PODs. |
| **Disputed Invoices (Exceptions)** | **3,126** (20.8%) | Flagged for contractual or operational discrepancies. |
| **Total Freight Spend Audited** | **$11,884,585.13** | Gross amount billed by transportation carriers. |
| **Approved Spend** | **$10,801,871.16** | Net verified spend according to contracted tariffs. |
| **Total Overcharges Identified** | **$1,083,601.32** | Hard dollar cost recovery contested via dispute memos. |
| **Audit Precision / Recall** | **100.0% / 100.0%** | Zero false negatives across all injected anomaly classes. |
| **Audit F1-Score** | **1.0000** | Optimal balance of precision and recall. |
| **Dollar Recovery Accuracy** | **99.15%** | Identified discrepancies reconcile directly to ground truth. |

---

## 2. Relational Entity Dataset Volume (Step 4 & 9)

| Entity Table | Generated Records | Primary Key Convention | Status |
| :--- | :--- | :--- | :--- |
| `carriers` | 100 | `CAR-000001` | Active & Verified |
| `lanes` | 150 | `LANE-000001` | US Freight Corridors |
| `rate_cards` | 33,250 | `RATE-<carrier>-2026-NNNN` | Contracted Weight Tiers |
| `shipments` | 20,000 | `SHP-2026-000001` | Operational Movements |
| `shipment_legs` | 20,000 | `LEG-SHP-2026-000001-01` | Terminal Departure/Arrivals |
| `weight_measurements` | 20,000 | `WM-SHP-2026-000001-01` | Scale & Dimensional Readings |
| `accessorials` | 6,286 | `ACC-000001` | Liftgate, Residential, Hazmat |
| `freight_invoices` | 15,000 | `FINV-2026-000001` | Carrier Bills Presented |
| `invoice_lines` | 34,180 | `FLINE-<inv>-01` | Itemized Base, FSC, Accessorials |
| `audit_exceptions` | 3,126 | `FEX-2026-000001` | Formal Dispute Exception Records |
| `credit_notes` | 692 | `CR-2026-000001` | Financial Recovery Artifacts |

---

## 3. Anomaly Detection & Exception Breakdown (Step 5)

| Exception Category | Ground Truth Count | Detected Count | Detection Rate | Typical Root Cause |
| :--- | :--- | :--- | :--- | :--- |
| `WEIGHT_TIER_MISMATCH` | 731 | 731 | **100.0%** | Carrier billed at a higher weight bracket rate or ignored dim weight. |
| `UNKNOWN_SHIPMENT` | 652 | 652 | **100.0%** | Carrier billed a shipment number not found in TMS master records. |
| `DUPLICATE_SURCHARGE` | 453 | 453 | **100.0%** | Redundant secondary fuel surcharge line added to single invoice. |
| `EXPIRED_RATE_CARD` | 462 | 462 | **100.0%** | Carrier billed using an expired contract tariff schedule. |
| `CREDIT_OVER_EXCEPTION` | 341 | 341 | **100.0%** | Credit note amount issued by carrier exceeds disputed exception total. |
| `UNAUTHORIZED_ACCESSORIAL` | 261 | 261 | **100.0%** | Accessorial billed without proof-of-delivery or shipper authorization. |
| `DUPLICATE_INVOICE` | 226 | 226 | **100.0%** | Duplicate invoice issued for previously billed freight shipment. |

---

## 4. Confusion Matrix & Decision Verification

- **True Positives (Disputes correctly flagged):** `3,126`
- **False Positives (Clean invoices mistakenly flagged):** `0`
- **True Negatives (Clean invoices approved cleanly):** `11,874`
- **False Negatives (Overcharges missed):** `0`

---

## 5. Credit Note & Financial Dispute Reconciliation

- **Total Credit Notes Reconciled:** `692`
- **Over-Credited Anomalies Caught:** `268`
- **Reconciliation Status:** All approved disputes mapped to carrier credit memos with audit trail traceability.
