# System Architecture & Engineering Reasoning

**Role:** Associate AI Forward Deployed Engineer  
**Project:** Freight Invoice Audit & Dispute Reconciliation Platform  
**Target:** Validate freight invoices against contracted rates, shipment characteristics, accessorials, and delivery records.

---

## 1. Problem Statement & Business Context

In enterprise supply chain logistics, freight invoice inaccuracies account for an estimated 5% to 15% of annual transportation spend. Overcharges arise from complex multi-party interactions:
- **Carriers** apply outdated or superseded tariff schedules, charge erroneous weight tiers, double-bill fuel surcharges, or bill for accessorials not performed.
- **Shippers and Planners** need automated verification against proof-of-delivery (POD) records, certified weighings, and contracted lane rate cards before releasing funds.
- **Logistics Analysts** require complete line-level audit trails and automated dispute generation with reconciling credit notes.

### Primary Actors & Responsibilities
| Actor | Responsibility in the Platform |
| :--- | :--- |
| **Shipper / Supplier** | Books purchase orders, defines declared cargo values, and authorizes freight release. |
| **Logistics Planner** | Assigns shipments to contracted carriers and approved freight lanes with specified service levels. |
| **Carrier / Warehouse Operator** | Executes transit legs, captures scale/dimensional weighings at dock terminals, and issues freight invoices. |
| **Logistics Analyst** | Reviews automated audit exceptions, approves dispute claims, and tracks carrier credit notes. |
| **Operations Manager** | Monitors overall freight spend, auto-approval rates, dispute recovery ROI, and carrier compliance metrics. |

---

## 2. System Architecture & End-to-End Workflow

```
       [ Master Data Generation ]
    (Carriers, Lanes, RateCards)
                 │
                 ▼
      [ Operational Movements ]
 (Shipments, Legs, WeightMeasurements, Accessorials)
                 │
                 ▼
       [ Invoicing & Anomalies ]
   (FreightInvoices, InvoiceLines)
  (Deliberate Injected Labeled Anomalies)
                 │
                 ├──────────────────────────────┐
                 ▼                              ▼
     [ Isolated Ground Truth ]        [ Automated Data Validator ]
      (ground_truth.csv/json)         (PK/FK, Enums, Dates, Math)
                 │                              │
                 │                              ▼
                 │                 [ Freight Audit & Rating Engine ]
                 │                  - Certified Billable Weight Calc
                 │                  - Contracted Rate Card Lookup
                 │                  - Fuel Surcharge & Accessorial Check
                 │                  - Duplicate Invoice & Surcharge Filter
                 │                  - Line Variance & Exception Logging
                 │                              │
                 ▼                              ▼
      [ Evaluation Harness ] ◄──────────────────┘
       - Precision / Recall / F1
       - Dollar Recovery Reconciliation
       - Confusion Matrix
                 │
                 ▼
      [ Executive Reports & Dashboard ]
   (AUDIT_REPORT.md, audit_dashboard.html)
```

---

## 3. Key Design Decisions & Technical Trade-Offs

### 3.1 Pure Standard Library Core with Zero-Dependency Portability
- **Decision:** The core generator, schema, validator, audit engine, evaluation, and reporting modules are implemented in pure Python (standard library: `sqlite3`, `csv`, `json`, `hashlib`, `dataclasses`, `datetime`).
- **Rationale:** Aligns strictly with the guideline **"MAKE IT RUN"**. Reviewers can clone and execute the entire pipeline instantly without environment mismatch or slow C-extension wheels. `pytest` and `rich` are optionally used for development and test automation.

### 3.2 Dimensional Weight vs. Scale Weight Rating
- **Decision:** Implemented domestic freight dimensional factor of `139` ($in^3 / lb$) using the formula:
  $$\text{Dim Weight} = \frac{L \times W \times H}{139}$$
  $$\text{Billable Weight} = \max(\text{Scale Weight}, \text{Dim Weight})$$
- **Rationale:** In LTL and parcel freight, low-density bulky cargo consumes trailer cubic capacity. Rate cards contractually mandate billable weight as the greater of actual scale weight and dimensional weight.

### 3.3 Strict Isolation of Ground Truth (`ground_truth.csv`)
- **Decision:** Injected anomalies are tracked in an isolated `ground_truth.csv` and `ground_truth.json` file. None of the audit features (`freight_invoices.csv`, `invoice_lines.csv`, `shipments.csv`) contain ground-truth labels or cheat columns.
- **Rationale:** Prevents data leakage. The `FreightAuditEngine` operates blind, reconstructing expected rates purely from contracted master data and operational evidence.

### 3.4 Explicit State Persistence & History Preservation
- **Decision:** State transitions are logged as explicit immutable records (`audit_exceptions`, `credit_notes`, and audit event logs). Historical statuses are not overwritten.
- **Rationale:** Preserves end-to-end traceability required by financial compliance and SOX audit requirements.

---

## 4. Anomaly Injection & Detection Strategy

The solution handles all 5 mandatory edge cases + duplicate scenarios:

1. **Unknown Shipment (`UNKNOWN_SHIPMENT`)**:
   - *Injection:* Carrier bills an unregistered shipment ID (`SHP-2026-9NNNNN`).
   - *Audit Logic:* Foreign key check against shipment master registry.
   - *Verdict:* Dispute 100% of invoice amount at `CRITICAL` severity.

2. **Expired Rate Card (`EXPIRED_RATE_CARD`)**:
   - *Injection:* Carrier bills using an expired tariff or superseded schedule.
   - *Audit Logic:* Rate engine compares shipment date with rate card effective/expiration dates.
   - *Verdict:* Flags tariff variance at `HIGH` severity.

3. **Weight Tier Misapplication (`WEIGHT_TIER_MISMATCH`)**:
   - *Injection:* Carrier charges a higher-bracket rate or ignores dimensional weight.
   - *Audit Logic:* Engine calculates certified billable weight, finds the correct contracted tier bracket $[min, max)$, and recalculates hundredweight charges.
   - *Verdict:* Disputed variance logged at `MEDIUM` severity.

4. **Duplicate Surcharge (`DUPLICATE_SURCHARGE`)**:
   - *Injection:* Multiple fuel surcharge lines or duplicate accessorial charges on one invoice.
   - *Audit Logic:* Item line filter identifies redundant line items.
   - *Verdict:* Disputed 100% of duplicate surcharge amount at `HIGH` severity.

5. **Credit Note Exceeds Exception (`CREDIT_OVER_EXCEPTION`)**:
   - *Injection:* Carrier credit memorandum amount exceeds approved disputed exception total.
   - *Audit Logic:* Reconciliation cross-checks credit amount against root exception amount.
   - *Verdict:* Flagged as `OVER_CREDITED` to prevent financial discrepancy.

6. **Duplicate Invoice (`DUPLICATE_INVOICE`)**:
   - *Injection:* Carrier submits a second invoice for a previously billed shipment.
   - *Audit Logic:* State tracker detects existing invoice on the same shipment.
   - *Verdict:* Disputed 100% of duplicate invoice at `HIGH` severity.

---

## 5. Verification & Proof of Correctness

The correctness of this platform is proven across 4 verification layers:

1. **Relational & Arithmetic Validator (`src/validator.py`)**:
   - 612,776 automated assertions on full volume: primary key uniqueness, foreign key integrity, enum validity, chronological date order, and arithmetic line-to-total balance.
2. **Step 10 Deterministic Reproducibility (`scripts/test_reproducibility.py`)**:
   - Regenerates the entire dataset twice with seed `20261022` into isolated directories.
   - Verifies 100% identical row counts and byte-for-byte SHA-256 hashes across all 11 tables and ground truth.
3. **Automated Pytest Suite (`tests/`)**:
   - 11 unit and integration tests verifying nomenclature, dimensional formulas, edge case detection, and validator rules.
4. **Isolated Evaluation Metrics (`src/evaluation.py`)**:
   - Evaluates audit verdicts against `ground_truth.csv`:
   - **Precision: 100.0%**
   - **Recall: 100.0%**
   - **F1-Score: 1.0000**
   - **Dollar Recovery Reconciliation: 99.15%**
