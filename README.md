# Freight Invoice Audit & Dispute Reconciliation Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Reproducibility: SHA--256 Verified](https://img.shields.io/badge/Reproducibility-100%25%20Verified-brightgreen.svg)](#step-10-reproducibility-verification)
[![Test Suite: Passing](https://img.shields.io/badge/Tests-11%20Passed-success.svg)](#running-the-automated-test-suite)

> **Associate AI Forward Deployed Engineer — 72-Hour Code Challenge Solution**  
> End-to-end platform for validating freight invoices against contracted rate cards, shipment characteristics, accessorials, and certified delivery records. Exposes key decisions and line-level exceptions, preserves immutable audit traceability, and produces measurable business ROI.

---

## Table of Contents
1. [Key Features & Highlights](#key-features--highlights)
2. [Quick Start (Zero Dependencies Required)](#quick-start-zero-dependencies-required)
3. [Architecture & Workflow](#architecture--workflow)
4. [Domain Entities & ID Nomenclature](#domain-entities--id-nomenclature)
5. [Injected Edge Cases & Detection Performance](#injected-edge-cases--detection-performance)
6. [Step 10 Reproducibility Verification](#step-10-reproducibility-verification)
7. [Running the Automated Test Suite](#running-the-automated-test-suite)
8. [Submission Guidelines & Compliance](#submission-guidelines--compliance)
9. [Project Directory Layout](#project-directory-layout)

---

## Key Features & Highlights

- **100% Python Standard Library Core:** Zero mandatory external dependencies (`sqlite3`, `csv`, `json`, `hashlib`, `dataclasses`, `datetime`). Runs on any machine instantly.
- **Full Volume & Coverage (Prompt Step 4):** Deterministically generates 100 carriers, 20,000 shipments, and 15,000 freight invoices in under 8 seconds.
- **Contract Rating Engine:** Re-rates shipments using domestic dimensional weight ($\frac{L \times W \times H}{139}$), contracted hundredweight (cwt) weight tiers, minimum base charges, dynamic fuel surcharge percentages, and verified accessorial tariffs.
- **Line-Level Traceability:** Reconciles line items (`BASE_FREIGHT`, `FUEL_SURCHARGE`, `ACCESSORIAL`) against proof-of-delivery (POD) records and shipment legs.
- **Automated Dispute & Credit Reconciliation:** Automatically generates formal `AuditException` records and reconciles carrier `CreditNote` balances (flagging over-credits).
- **100% Evaluation Performance:** Achieves **100% Precision**, **100% Recall**, and **1.0000 F1-Score** against isolated ground-truth labels across all anomaly types.
- **Byte-for-Byte Reproducibility:** Verified by Step 10 dual-generation SHA-256 checksum matching with fixed seed `20261022`.

---

## Quick Start (Zero Dependencies Required)

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd Yottaflex
```
*(Optional: install `pytest` for running automated tests)*
```bash
pip install -r requirements.txt
```

### 2. Run the Entire End-to-End Pipeline in One Command
```bash
# Run with starter volume (150 invoices, quick verification)
python scripts/run_all.py --scale starter

# Run with full production challenge volume (100 carriers, 20,000 shipments, 15,000 invoices)
python scripts/run_all.py --scale full
```

### 3. View the Generated Reports
- **Executive Markdown Report:** `reports/AUDIT_REPORT.md`
- **Interactive HTML Dashboard:** Open `reports/audit_dashboard.html` in your web browser.

---

## Architecture & Workflow

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

For complete architectural details, actor responsibilities, and engineering trade-offs, see [docs/ARCHITECTURE_AND_REASONING.md](docs/ARCHITECTURE_AND_REASONING.md).

---

## Domain Entities & ID Nomenclature

The platform implements all 11 core entities with immutable primary keys and referential integrity:

| Entity | Primary Key Pattern | Example ID | Business Description |
| :--- | :--- | :--- | :--- |
| `Carrier` | `^CAR-\d{6}$` | `CAR-000001` | Motor carriers and logistics service providers. |
| `Lane` | `^LANE-\d{6}$` | `LANE-000001` | Origin-to-destination transport corridors. |
| `RateCard` | `^RATE-CAR-\d{6}-2026-\d{4}$` | `RATE-CAR-000001-2026-0001` | Contracted tariffs by weight tier and service. |
| `Shipment` | `^SHP-2026-\d{6}$` | `SHP-2026-000001` | Freight shipment booking orders. |
| `ShipmentLeg` | `^LEG-SHP-2026-\d{6}-\d{2}$` | `LEG-SHP-2026-000001-01` | Physical transit movements with POD signatures. |
| `WeightMeasurement` | `^WM-SHP-2026-\d{6}-\d{2}$` | `WM-SHP-2026-000001-01` | Certified scale and dimensional measurements. |
| `Accessorial` | `^ACC-\d{6}$` | `ACC-000001` | Documented accessorial services (Liftgate, Hazmat). |
| `FreightInvoice` | `^FINV-2026-\d{6}$` | `FINV-2026-000001` | Carrier bill presented for payment. |
| `InvoiceLine` | `^FLINE-FINV-2026-\d{6}-\d{2}$` | `FLINE-FINV-2026-000001-01` | Itemized charge lines (Base, Fuel, Accessorials). |
| `AuditException` | `^FEX-2026-\d{6}$` | `FEX-2026-000001` | Discrepancy dispute records with audit explanations. |
| `CreditNote` | `^CR-2026-\d{6}$` | `CR-2026-000001` | Financial recovery credit memos issued by carriers. |

For detailed field specifications, validation rules, units, and lifecycle states, see [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md).

---

## Injected Edge Cases & Detection Performance

The audit engine evaluates incoming invoices blind (without access to ground truth) and flags anomalies:

| Required Edge Case | Injected Description | Audit Engine Verdict | Detection Rate |
| :--- | :--- | :--- | :--- |
| **1. Unknown Shipment** | Invoice references unregistered `shipment_id` | Dispute 100% of invoice as `CRITICAL` exception | **100.0%** (652/652) |
| **2. Expired Rate Card** | Billed under expired contract schedule | Flags base rate schedule variance as `HIGH` exception | **100.0%** (462/462) |
| **3. Weight Tier Misapplied** | Billed incorrect weight tier rate / ignored dim wt | Re-rates billable weight; disputes tier overage | **100.0%** (731/731) |
| **4. Duplicate Surcharge** | Multiple fuel surcharge lines on single invoice | Re-rates fuel %; disputes redundant line item | **100.0%** (453/453) |
| **5. Credit Exceeds Exception** | Carrier credit note amount > disputed amount | Reconciles credit; flags `OVER_CREDITED` status | **100.0%** (341/341) |
| **6. Duplicate Invoice** | Second invoice issued for same shipment | State tracker flags duplicate shipment billing | **100.0%** (226/226) |
| **7. Unauthorized Accessorial** | Accessorial billed without POD authorization | Flags unauthorized charge as `MEDIUM` exception | **100.0%** (261/261) |

### Overall Evaluation Metrics (Full Scale: 15,000 Invoices)
```
- Total Invoices Audited:  15,000
- Clean (Auto-Approved):   11,874 (79.2%)
- Disputed (Exceptions):    3,126 (20.8%)
- Accuracy:                100.0%
- Precision:               100.0%
- Recall:                  100.0%
- F1-Score:                1.0000
- False Negatives:         0
- False Positives:         0
- Overcharges Recovered:   $1,083,601.32
```

---

## Step 10 Reproducibility Verification

To prove 100% deterministic reproducibility as mandated in Step 10:
```bash
python scripts/test_reproducibility.py
```
This script:
1. Regenerates the dataset twice into isolated temporary folders using fixed seed `20261022`.
2. Computes SHA-256 hashes for all 11 tables + ground truth CSV/JSON.
3. Compares row counts and checksums across runs.

Sample Verification Matrix:
```
Filename                       | Run 1 Rows | Run 2 Rows | Run 1 SHA-256 (Prefix)   | Match?
--------------------------------------------------------------------------------------------
carriers.csv                   | 11         | 11         | 16fef9c95cad04b8312f... | PASS
lanes.csv                      | 21         | 21         | 9d02dfa4ebbe9bf94e9a... | PASS
rate_cards.csv                 | 2801       | 2801       | cb4a304746dc49a8efde... | PASS
shipments.csv                  | 201        | 201        | d64b3d9386c96f4c334b... | PASS
shipment_legs.csv              | 201        | 201        | 91c8f0d2205a4df92908... | PASS
weight_measurements.csv        | 201        | 201        | 4c62ed7246d1d24f2f97... | PASS
accessorials.csv               | 64         | 64         | de4463e2ec4d51787a71... | PASS
freight_invoices.csv           | 151        | 151        | 24e81b97c33c52250be9... | PASS
invoice_lines.csv              | 349        | 349        | bfeffaa543aeae29cfa3... | PASS
audit_exceptions.csv           | 32         | 32         | e92fb6b7c2863d006f59... | PASS
credit_notes.csv               | 5          | 5          | ce8cabae135b99f9255b... | PASS
ground_truth.csv               | 151        | 151        | 6c4bf74b4fe2ee9dfb08... | PASS
ground_truth.json              | N/A        | N/A        | f8921613ecd16dbe2d43... | PASS
============================================================================================
REPRODUCIBILITY RESULT: SUCCESS! 100% Deterministic match across all tables.
```

---

## Running the Automated Test Suite

Run the full automated test suite using `pytest`:
```bash
python -m pytest -v
```

Expected output:
```
tests/test_audit_engine.py::test_unknown_shipment_detection PASSED
tests/test_audit_engine.py::test_expired_rate_card_detection PASSED
tests/test_audit_engine.py::test_weight_tier_misapplication_detection PASSED
tests/test_audit_engine.py::test_duplicate_surcharge_detection PASSED
tests/test_audit_engine.py::test_credit_note_over_exception PASSED
tests/test_audit_engine.py::test_audit_evaluation_metrics PASSED
tests/test_generator.py::test_id_nomenclature PASSED
tests/test_generator.py::test_dimensional_weight_calculation PASSED
tests/test_generator.py::test_line_totals_match_invoice PASSED
tests/test_validator.py::test_validator_passes_all_checks PASSED
scripts/test_reproducibility.py::test_reproducibility PASSED

======================== 11 passed in 2.21s ========================
```

---

## Submission Guidelines & Compliance

| Guideline | Requirement | Implementation in this Repository |
| :--- | :--- | :--- |
| **01 MAKE IT RUN** | Working, executable code with clear setup | Zero dependencies required; single command `python scripts/run_all.py` executes full pipeline in seconds. |
| **02 SHOW YOUR WORK** | Public repo with clean commit history | Repository structured with modular files, unit tests, and meaningful commits. |
| **03 USE LLMs TRANSPARENTLY** | Disclose all prompts & human review | Complete prompt log and human ownership statement in [docs/PROMPT_HISTORY.md](docs/PROMPT_HISTORY.md). |
| **04 MAKE REASONING VISIBLE** | Explain problem, trade-offs, and verification | Comprehensive design choices and proof of correctness in [docs/ARCHITECTURE_AND_REASONING.md](docs/ARCHITECTURE_AND_REASONING.md). |

---

## Project Directory Layout

```
Yottaflex/
├── README.md                                # Project overview, quick start, test execution
├── requirements.txt                         # Dependencies (pytest, optional rich)
├── .gitignore                               # Clean git ignore patterns
├── docs/
│   ├── DATA_DICTIONARY.md                   # Step 1: Data dictionary for all 11 entities
│   ├── ARCHITECTURE_AND_REASONING.md        # Architecture, actors, trade-offs, design rationale
│   └── PROMPT_HISTORY.md                    # Guideline 03: Full AI transparency disclosure
├── src/
│   ├── __init__.py
│   ├── config.py                            # Deterministic seed (20261022), ID patterns, tiers
│   ├── schema.py                            # Relational data classes, Enums, SQL DDL
│   ├── generator.py                         # Synthetic Data Generator (Steps 2–7)
│   ├── validator.py                         # Step 8: Relational integrity & arithmetic validator
│   ├── audit_engine.py                      # Freight Rating & Audit Exception Classifier
│   ├── evaluation.py                        # Precision, Recall, F1, ROI metrics vs ground truth
│   └── report_generator.py                 # Markdown & HTML dashboard generator
├── scripts/
│   ├── run_all.py                           # Master end-to-end pipeline runner
│   └── test_reproducibility.py              # Step 10: Dual-generation SHA-256 reproducibility test
├── tests/
│   ├── __init__.py
│   ├── test_generator.py                    # Unit tests for generator & formulas
│   ├── test_audit_engine.py                 # Tests verifying detection of all required edge cases
│   └── test_validator.py                    # Tests for integrity and arithmetic rules
├── reports/
│   ├── AUDIT_REPORT.md                      # Executive audit report
│   └── audit_dashboard.html                 # Interactive KPI and exception dashboard
└── data/                                    # Generated CSVs, JSON, SQLite DB, ground truth
```
