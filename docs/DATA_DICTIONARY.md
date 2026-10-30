# Data Dictionary: Freight Invoice Audit & Reconciliation System

This data dictionary defines the 11 core entities, attributes, relationships, cardinalities, units, allowed enums, lifecycle states, and domain validation rules for the Freight Invoice Audit System.

---

## 1. Entity-Relationship Overview

```
 [Carrier] 1 ──── N [RateCard] N ──── 1 [Lane]
    │ 1                                     │ 1
    │                                       │
    │ 1                                     │ N
    └─────────────── N [Shipment] ──────────┘
                         │ 1
        ┌────────────────┼────────────────┬────────────────┐
        │ 1              │ 1              │ 1              │ 1
        ▼ N              ▼ N              ▼ N              ▼ N
 [ShipmentLeg]    [WeightMeasurement] [Accessorial]   [FreightInvoice]
                                                           │ 1
                                             ┌─────────────┴─────────────┐
                                             ▼ N                         ▼ N
                                      [InvoiceLine]               [AuditException]
                                                                         │ 1
                                                                         ▼ 0..N
                                                                    [CreditNote]
```

### Cardinality Summary
- **Carrier to RateCard**: `1 : N` (A carrier has multiple lane/tier rate cards).
- **Lane to RateCard**: `1 : N` (A lane is serviced by multiple carrier rate cards).
- **Lane to Shipment**: `1 : N` (Multiple shipments move across a defined lane).
- **Carrier to Shipment**: `1 : N` (Contracted carrier assigned to shipment).
- **Shipment to ShipmentLeg**: `1 : N` (A shipment has one or more sequential transport legs).
- **Shipment to WeightMeasurement**: `1 : N` (Actual scale and dimensional weighings per shipment/leg).
- **Shipment to Accessorial**: `1 : N` (Documented and authorized accessorial events).
- **Shipment to FreightInvoice**: `1 : N` (Standard 1:1, but N allows testing duplicate billing anomalies).
- **FreightInvoice to InvoiceLine**: `1 : N` (Itemized charges: base, fuel, accessorials, taxes).
- **FreightInvoice to AuditException**: `1 : N` (Discrepancies identified during audit).
- **AuditException to CreditNote**: `1 : 0..1` (Credit recovery linked to an approved exception dispute).

---

## 2. Entity Specifications (Step 1 Detailed Fields)

### 2.1 Carrier (`carriers`)
Master table defining transportation service providers.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `carrier_id` | STRING(32) | Required | Pattern `^CAR-\d{6}$` | N/A | **Primary Key** | Must follow `CAR-000001` format. |
| `name` | STRING(128) | Required | Non-empty alphanumeric string | N/A | Unique | Commercial carrier legal name. |
| `scac` | STRING(4) | Required | 2 to 4 uppercase letters `^[A-Z]{2,4}$` | N/A | Unique | Standard Carrier Alpha Code. |
| `mode` | ENUM | Required | `FTL`, `LTL`, `PARCEL`, `INTERMODAL` | N/A | Non-unique | Primary operational mode. |
| `contact_email` | STRING(128) | Required | Valid RFC 5322 email | N/A | Non-unique | Must contain `@` and valid domain. |
| `status` | ENUM | Required | `ACTIVE`, `SUSPENDED`, `TERMINATED` | N/A | Non-unique | Inactive carriers cannot take new shipments. |
| `created_at` | TIMESTAMP | Required | ISO 8601 UTC string | N/A | Non-unique | Must be valid datetime `<= CURRENT_TIMESTAMP`. |

---

### 2.2 Lane (`lanes`)
Master table defining origin-to-destination freight corridors.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `lane_id` | STRING(32) | Required | Pattern `^LANE-\d{6}$` | N/A | **Primary Key** | Must follow `LANE-000001` format. |
| `origin_city` | STRING(64) | Required | Non-empty string | N/A | Non-unique | e.g. Chicago, Atlanta, Dallas. |
| `origin_state` | STRING(2) | Required | 2-letter US State abbreviation `^[A-Z]{2}$` | N/A | Non-unique | Valid US State code. |
| `origin_zip` | STRING(5) | Required | 5-digit US postal code `^\d{5}$` | N/A | Non-unique | Valid 5-digit zip code. |
| `destination_city` | STRING(64) | Required | Non-empty string | N/A | Non-unique | Delivery metro city. |
| `destination_state`| STRING(2) | Required | 2-letter US State abbreviation `^[A-Z]{2}$` | N/A | Non-unique | Valid US State code. |
| `destination_zip` | STRING(5) | Required | 5-digit US postal code `^\d{5}$` | N/A | Non-unique | Valid 5-digit zip code. |
| `distance_miles` | DECIMAL(10,2)| Required | Range `[1.00, 4000.00]` | Miles | Non-unique | Positive distance between points. |
| `transit_days` | INTEGER | Required | Range `[1, 14]` | Days | Non-unique | Expected transit duration. |

---

### 2.3 RateCard (`rate_cards`)
Contracted freight pricing schedule by carrier, lane, service level, and weight tier.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `rate_card_id` | STRING(64) | Required | Pattern `^RATE-CAR-\d{6}-\d{4}-\d{2}$` | N/A | **Primary Key** | Matches convention `RATE-<carrier-id>-YYYY-NN`. |
| `carrier_id` | STRING(32) | Required | FK -> `carriers.carrier_id` | N/A | Non-unique | Must reference active carrier. |
| `lane_id` | STRING(32) | Required | FK -> `lanes.lane_id` | N/A | Non-unique | Must reference valid lane. |
| `service_level` | ENUM | Required | `STANDARD_GROUND`, `EXPEDITED`, `NEXT_DAY_AIR`, `ECONOMY` | N/A | Non-unique | Contracted transit service tier. |
| `min_charge_usd` | DECIMAL(10,2)| Required | `>= 25.00` | USD | Non-unique | Minimum baseline invoice charge. |
| `weight_tier_min_lbs`| DECIMAL(10,2)| Required | `>= 0.00` | Pounds (lbs)| Non-unique | Lower boundary of weight bracket (inclusive). |
| `weight_tier_max_lbs`| DECIMAL(10,2)| Required | `> weight_tier_min_lbs` | Pounds (lbs)| Non-unique | Upper boundary of weight bracket (exclusive). |
| `rate_per_cwt_usd`| DECIMAL(10,2)| Required | `> 0.00` | USD / cwt | Non-unique | Hundredweight rate (per 100 lbs). |
| `fuel_surcharge_percent`| DECIMAL(5,4)| Required | Range `[0.0000, 0.4500]` | Ratio (0-1) | Non-unique | Contracted fuel surcharge index rate. |
| `dim_factor` | INTEGER | Required | `139` or `166` | $in^3 / lb$ | Non-unique | Domestic freight dimensional divisor. |
| `effective_date`| DATE | Required | ISO 8601 `YYYY-MM-DD` | N/A | Non-unique | Rate card contract start date. |
| `expiration_date`| DATE | Required | ISO 8601 `YYYY-MM-DD` | N/A | Non-unique | Must be strictly `>= effective_date`. |
| `status` | ENUM | Required | `ACTIVE`, `EXPIRED`, `SUPERSEDED` | N/A | Non-unique | State of rate card. |

---

### 2.4 Shipment (`shipments`)
Operational shipment booking created by planners/shippers.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `shipment_id` | STRING(32) | Required | Pattern `^SHP-\d{4}-\d{6}$` | N/A | **Primary Key** | Matches convention `SHP-2026-000001`. |
| `carrier_id` | STRING(32) | Required | FK -> `carriers.carrier_id` | N/A | Non-unique | Must reference valid carrier. |
| `lane_id` | STRING(32) | Required | FK -> `lanes.lane_id` | N/A | Non-unique | Must reference valid lane. |
| `service_level` | ENUM | Required | `STANDARD_GROUND`, `EXPEDITED`, `NEXT_DAY_AIR`, `ECONOMY` | N/A | Non-unique | Must match available carrier services. |
| `shipment_date` | DATE | Required | ISO 8601 `YYYY-MM-DD` | N/A | Non-unique | Date cargo was tendered. |
| `delivery_date` | DATE | Optional | ISO 8601 `YYYY-MM-DD` | N/A | Non-unique | Must be `>= shipment_date`. |
| `pieces_count` | INTEGER | Required | `>= 1` | Pieces | Non-unique | Number of packages/handling units. |
| `pallet_count` | INTEGER | Required | `>= 0` | Pallets | Non-unique | Number of pallets loaded. |
| `declared_value_usd`| DECIMAL(12,2)| Required | `>= 0.00` | USD | Non-unique | Valuation for insurance liability. |
| `status` | ENUM | Required | `BOOKED`, `IN_TRANSIT`, `DELIVERED`, `EXCEPTION`, `CANCELLED` | N/A | Non-unique | Shipment lifecycle status. |
| `created_at` | TIMESTAMP | Required | ISO 8601 UTC | N/A | Non-unique | Booking creation timestamp. |

---

### 2.5 ShipmentLeg (`shipment_legs`)
Sequential physical transportation movements fulfilling a shipment.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `leg_id` | STRING(48) | Required | Pattern `^LEG-SHP-\d{4}-\d{6}-\d{2}$`| N/A | **Primary Key** | Deterministic leg ID. |
| `shipment_id` | STRING(32) | Required | FK -> `shipments.shipment_id`| N/A | Non-unique | Must reference valid shipment. |
| `leg_sequence` | INTEGER | Required | `>= 1` | Index | Non-unique | 1 for origin-to-hub, 2 for linehaul, etc. |
| `carrier_id` | STRING(32) | Required | FK -> `carriers.carrier_id` | N/A | Non-unique | Carrier handling leg. |
| `origin_terminal`| STRING(64) | Required | Non-empty string | N/A | Non-unique | Dispatch terminal location. |
| `dest_terminal` | STRING(64) | Required | Non-empty string | N/A | Non-unique | Receiving terminal location. |
| `departure_time`| TIMESTAMP | Required | ISO 8601 UTC | N/A | Non-unique | Must be `>= shipment.shipment_date`. |
| `arrival_time` | TIMESTAMP | Optional | ISO 8601 UTC | N/A | Non-unique | Must be `>= departure_time`. |
| `pod_signature` | STRING(64) | Optional | Non-empty alphanumeric string | N/A | Non-unique | Receiver signature hash/name on final leg. |
| `status` | ENUM | Required | `SCHEDULED`, `IN_TRANSIT`, `COMPLETED`, `DELAYED` | N/A | Non-unique | Leg execution state. |

---

### 2.6 WeightMeasurement (`weight_measurements`)
Certified dimensional and scale readings captured at warehouse docks or scale terminals.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `measurement_id`| STRING(48) | Required | Pattern `^WM-SHP-\d{4}-\d{6}-\d{2}$` | N/A | **Primary Key** | Unique measurement event identifier. |
| `shipment_id` | STRING(32) | Required | FK -> `shipments.shipment_id`| N/A | Non-unique | Must reference valid shipment. |
| `length_in` | DECIMAL(8,2) | Required | `> 0.00` | Inches | Non-unique | Package bounding box length. |
| `width_in` | DECIMAL(8,2) | Required | `> 0.00` | Inches | Non-unique | Package bounding box width. |
| `height_in` | DECIMAL(8,2) | Required | `> 0.00` | Inches | Non-unique | Package bounding box height. |
| `scale_weight_lbs`| DECIMAL(10,2)| Required | `> 0.00` | Pounds | Non-unique | Physical certified scale weight. |
| `dim_weight_lbs` | DECIMAL(10,2)| Required | `> 0.00` | Pounds | Non-unique | Derived: `(length_in * width_in * height_in) / dim_factor`. |
| `billable_weight_lbs`| DECIMAL(10,2)| Required| `> 0.00` | Pounds | Non-unique | Derived: `max(scale_weight_lbs, dim_weight_lbs)`. |
| `weighed_by` | ENUM | Required | `SCALE_TERMINAL`, `WAREHOUSE_RECEIVING`, `SHIPPER_DOCK` | N/A | Non-unique | Measurement origin authority. |
| `measured_at` | TIMESTAMP | Required | ISO 8601 UTC | N/A | Non-unique | Measurement capture timestamp. |

---

### 2.7 Accessorial (`accessorials`)
Operational accessorial services performed and documented for a shipment.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `accessorial_id`| STRING(32) | Required | Pattern `^ACC-\d{6}$` | N/A | **Primary Key** | Unique accessorial service event ID. |
| `shipment_id` | STRING(32) | Required | FK -> `shipments.shipment_id`| N/A | Non-unique | Must reference valid shipment. |
| `service_code` | ENUM | Required | `LIFTGATE`, `RESIDENTIAL`, `INSIDE_PICKUP`, `HAZMAT`, `DETENTION`, `REDELIVERY`, `STORAGE` | N/A | Non-unique | Standard NMFTA/industry charge code. |
| `authorized` | BOOLEAN | Required | `TRUE`, `FALSE` | N/A | Non-unique | Indicates if approved on Bill of Lading / POD. |
| `contract_rate_usd`| DECIMAL(10,2)| Required | `>= 0.00` | USD | Non-unique | Contracted baseline tariff for service. |
| `performed_at` | TIMESTAMP | Required | ISO 8601 UTC | N/A | Non-unique | Timestamp service was rendered. |
| `notes` | STRING(255) | Optional | Free text string | N/A | Non-unique | Driver or dispatcher remarks. |

---

### 2.8 FreightInvoice (`freight_invoices`)
Carrier bill presented to shipper/supplier for payment.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `invoice_id` | STRING(32) | Required | Pattern `^FINV-\d{4}-\d{6}$` | N/A | **Primary Key** | Matches convention `FINV-2026-000001`. |
| `carrier_id` | STRING(32) | Required | FK -> `carriers.carrier_id` | N/A | Non-unique | Invoicing carrier. |
| `shipment_id` | STRING(32) | Required | FK -> `shipments.shipment_id` (may violate in injected anomalies) | N/A | Non-unique | Referenced freight shipment. |
| `invoice_date` | DATE | Required | ISO 8601 `YYYY-MM-DD` | N/A | Non-unique | Date invoice issued by carrier. |
| `due_date` | DATE | Required | ISO 8601 `YYYY-MM-DD` | N/A | Non-unique | Must be `>= invoice_date` (Net 30/60). |
| `total_billed_usd`| DECIMAL(12,2)| Required| `>= 0.00` | USD | Non-unique | Derived: sum of `invoice_lines.billed_amount_usd`. |
| `total_expected_usd`| DECIMAL(12,2)| Required| `>= 0.00` | USD | Non-unique | Derived by audit rating engine. |
| `variance_usd` | DECIMAL(12,2)| Required | Any real number | USD | Non-unique | Derived: `total_billed_usd - total_expected_usd`. |
| `audit_status` | ENUM | Required | `PENDING`, `AUDITED_CLEAN`, `DISPUTED`, `AUTO_APPROVED`, `RESOLVED` | N/A | Non-unique | Lifecycle state of invoice audit. |
| `created_at` | TIMESTAMP | Required | ISO 8601 UTC | N/A | Non-unique | Ingestion timestamp. |

---

### 2.9 InvoiceLine (`invoice_lines`)
Itemized line-item charges comprising an invoice.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `line_id` | STRING(48) | Required | Pattern `^FLINE-FINV-\d{4}-\d{6}-\d{2}$`| N/A | **Primary Key** | Matches `FLINE-<invoice-id>-NN`. |
| `invoice_id` | STRING(32) | Required | FK -> `freight_invoices.invoice_id` | N/A | Non-unique | Parent invoice reference. |
| `line_number` | INTEGER | Required | `>= 1` | Index | Non-unique | Sequence within invoice. |
| `line_type` | ENUM | Required | `BASE_FREIGHT`, `FUEL_SURCHARGE`, `ACCESSORIAL`, `DISCOUNT`, `TAX` | N/A | Non-unique | Charge categorization. |
| `charge_code` | STRING(32) | Required | e.g. `BASE`, `FSC`, `LIFTGATE`, `RESIDENTIAL`, `DETENTION` | N/A | Non-unique | Standard code. |
| `description` | STRING(128) | Required | Descriptive charge text | N/A | Non-unique | Human readable description. |
| `billed_rate` | DECIMAL(10,2)| Required | `>= 0.00` | USD or % | Non-unique | Billed unit tariff or rate. |
| `billed_quantity`| DECIMAL(10,2)| Required | `>= 0.00` | cwt / Count / Flat | Non-unique | Volume or multiplier. |
| `billed_amount_usd`| DECIMAL(12,2)| Required | `>= 0.00` | USD | Non-unique | Line total charged. |
| `expected_amount_usd`| DECIMAL(12,2)| Required| `>= 0.00` | USD | Non-unique | Derived by audit re-rating engine. |
| `variance_usd` | DECIMAL(12,2)| Required | Real number | USD | Non-unique | `billed_amount_usd - expected_amount_usd`. |
| `line_status` | ENUM | Required | `VALIDATED`, `VARIANCE_DETECTED`, `DUPLICATE` | N/A | Non-unique | Audit verdict for line item. |

---

### 2.10 AuditException (`audit_exceptions`)
Detailed dispute and discrepancy record logged against an invoice.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `exception_id` | STRING(32) | Required | Pattern `^FEX-\d{4}-\d{6}$` | N/A | **Primary Key** | Matches convention `FEX-2026-000001`. |
| `invoice_id` | STRING(32) | Required | FK -> `freight_invoices.invoice_id` | N/A | Non-unique | Target audited invoice. |
| `line_id` | STRING(48) | Optional | FK -> `invoice_lines.line_id` | N/A | Non-unique | Nullable if invoice-level exception. |
| `exception_code`| ENUM | Required | `UNKNOWN_SHIPMENT`, `EXPIRED_RATE_CARD`, `WEIGHT_TIER_MISMATCH`, `DUPLICATE_SURCHARGE`, `DUPLICATE_INVOICE`, `UNAUTHORIZED_ACCESSORIAL`, `BASE_RATE_OVERCHARGE`, `CREDIT_OVER_EXCEPTION` | N/A | Non-unique | Standard exception category. |
| `severity` | ENUM | Required | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | N/A | Non-unique | Priority for logistics analyst review. |
| `disputed_amount_usd`| DECIMAL(12,2)| Required | `> 0.00` | USD | Non-unique | Overcharge amount contested. |
| `explanation` | STRING(512) | Required | Plain language reasoning | N/A | Non-unique | Mathematical and contractual explanation. |
| `status` | ENUM | Required | `DETECTED`, `UNDER_REVIEW`, `APPROVED_DISPUTE`, `REJECTED_DISPUTE`, `RESOLVED` | N/A | Non-unique | Dispute lifecycle stage. |
| `created_at` | TIMESTAMP | Required | ISO 8601 UTC | N/A | Non-unique | Exception generation timestamp. |
| `resolved_at` | TIMESTAMP | Optional | ISO 8601 UTC | N/A | Non-unique | Must be `>= created_at` when resolved. |

---

### 2.11 CreditNote (`credit_notes`)
Financial recovery artifact issued by carrier to reconcile an approved audit dispute.

| Field Name | Type | Required? | Allowed Values / Enums | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `credit_note_id`| STRING(32) | Required | Pattern `^CR-\d{4}-\d{6}$` | N/A | **Primary Key** | Matches convention `CR-2026-000001`. |
| `carrier_id` | STRING(32) | Required | FK -> `carriers.carrier_id` | N/A | Non-unique | Issuing carrier. |
| `invoice_id` | STRING(32) | Required | FK -> `freight_invoices.invoice_id` | N/A | Non-unique | Invoice being credited. |
| `exception_id` | STRING(32) | Required | FK -> `audit_exceptions.exception_id`| N/A | Non-unique | Root exception being reconciled. |
| `credit_amount_usd`| DECIMAL(12,2)| Required| `> 0.00` | USD | Non-unique | Value refunded/credited. |
| `credit_date` | DATE | Required | ISO 8601 `YYYY-MM-DD` | N/A | Non-unique | Date credit memorandum posted. |
| `reconciliation_status`| ENUM | Required| `RECONCILED`, `OVER_CREDITED`, `UNDER_CREDITED`, `DISPUTED` | N/A | Non-unique | Audit validation of credit balance. |
| `notes` | STRING(255) | Optional | Text | N/A | Non-unique | Settlement notes. |
| `created_at` | TIMESTAMP | Required | ISO 8601 UTC | N/A | Non-unique | Ingestion timestamp. |

---

## 3. Lifecycle States & State Transitions

### Freight Invoice Lifecycle
```
[PENDING]
    │
    ▼ (Run Audit Engine)
  ┌─────────────────────────┬─────────────────────────┐
  │ No Variance Detected    │ Discrepancy Found       │ Duplicate Detected
  ▼                         ▼                         ▼
[AUDITED_CLEAN]       [DISPUTED]               [DISPUTED]
  │                         │
  ▼ (Auto-Pay)              ▼ (Logistics Analyst Review)
[AUTO_APPROVED]       ┌─────────────────────────┐
                      │ Approved Dispute        │ Rejected Dispute
                      ▼                         ▼
               [APPROVED_DISPUTE]        [RESOLVED]
                      │ (Credit Note Issued)
                      ▼
               [RESOLVED]
```

### Audit Exception Lifecycle
```
[DETECTED] ──> [UNDER_REVIEW] ──> [APPROVED_DISPUTE] ──> [RESOLVED]
                                └──> [REJECTED_DISPUTE] ──> [RESOLVED]
```

### Injected Anomaly Rules (Ground Truth)
Deliberate negative test cases are injected with exact tags in `ground_truth.csv`:
1. `UNKNOWN_SHIPMENT`: Invoice specifies an invalid / non-existent `shipment_id`.
2. `EXPIRED_RATE_CARD`: Invoice rated against a rate card whose expiration date precedes the shipment pickup date.
3. `WEIGHT_TIER_MISMATCH`: Carrier applied a rate for a higher weight bracket or ignored dimensional weight.
4. `DUPLICATE_SURCHARGE`: Fuel surcharge or handling accessorial billed twice on separate lines for the same invoice.
5. `CREDIT_OVER_EXCEPTION`: Carrier issued a credit note whose amount exceeds the total disputed amount on the exception.

