"""
Comprehensive Data Validator for Freight Invoice Audit Dataset (Step 8).
Validates:
1. Primary key uniqueness
2. Foreign key referential integrity
3. Allowed enum domains
4. Chronological date ordering
5. Arithmetic reconciliation (totals, balances, line sums, dimensional weight)
6. Duplicate invoice and line checks
"""
import csv
import datetime
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_DIR
from src.schema import (
    CarrierMode, CarrierStatus, ServiceLevel, RateCardStatus,
    ShipmentStatus, LegStatus, WeighedBy, AccessorialCode,
    InvoiceAuditStatus, InvoiceLineType, ExceptionCode,
    ExceptionSeverity, ExceptionStatus, CreditReconciliationStatus
)

class DataValidator:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.issues: List[Dict[str, Any]] = []
        self.summary: Dict[str, Any] = {
            "checks_performed": 0,
            "checks_passed": 0,
            "violations_found": 0,
            "injected_anomalies_confirmed": 0,
            "validation_passed": True
        }

    def _read_csv(self, filename: str) -> List[Dict[str, str]]:
        path = self.data_dir / filename
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def validate_all(self) -> Dict[str, Any]:
        """Execute full suite of data integrity checks."""
        carriers = self._read_csv("carriers.csv")
        lanes = self._read_csv("lanes.csv")
        rate_cards = self._read_csv("rate_cards.csv")
        shipments = self._read_csv("shipments.csv")
        legs = self._read_csv("shipment_legs.csv")
        measurements = self._read_csv("weight_measurements.csv")
        accessorials = self._read_csv("accessorials.csv")
        invoices = self._read_csv("freight_invoices.csv")
        lines = self._read_csv("invoice_lines.csv")
        exceptions = self._read_csv("audit_exceptions.csv")
        credit_notes = self._read_csv("credit_notes.csv")
        ground_truth = self._read_csv("ground_truth.csv")

        # 1. Primary Key Uniqueness
        self._check_pk_uniqueness("carriers", carriers, "carrier_id")
        self._check_pk_uniqueness("lanes", lanes, "lane_id")
        self._check_pk_uniqueness("rate_cards", rate_cards, "rate_card_id")
        self._check_pk_uniqueness("shipments", shipments, "shipment_id")
        self._check_pk_uniqueness("shipment_legs", legs, "leg_id")
        self._check_pk_uniqueness("weight_measurements", measurements, "measurement_id")
        self._check_pk_uniqueness("accessorials", accessorials, "accessorial_id")
        self._check_pk_uniqueness("freight_invoices", invoices, "invoice_id")
        self._check_pk_uniqueness("invoice_lines", lines, "line_id")
        self._check_pk_uniqueness("audit_exceptions", exceptions, "exception_id")
        self._check_pk_uniqueness("credit_notes", credit_notes, "credit_note_id")

        # 2. Foreign Key Integrity
        carrier_ids = {c["carrier_id"] for c in carriers}
        lane_ids = {l["lane_id"] for l in lanes}
        shipment_ids = {s["shipment_id"] for s in shipments}
        invoice_ids = {i["invoice_id"] for i in invoices}
        exception_ids = {e["exception_id"] for e in exceptions}

        self._check_fk("rate_cards", rate_cards, "carrier_id", carrier_ids, "carriers")
        self._check_fk("rate_cards", rate_cards, "lane_id", lane_ids, "lanes")
        self._check_fk("shipments", shipments, "carrier_id", carrier_ids, "carriers")
        self._check_fk("shipments", shipments, "lane_id", lane_ids, "lanes")
        self._check_fk("shipment_legs", legs, "shipment_id", shipment_ids, "shipments")
        self._check_fk("weight_measurements", measurements, "shipment_id", shipment_ids, "shipments")
        self._check_fk("accessorials", accessorials, "shipment_id", shipment_ids, "shipments")
        self._check_fk("invoice_lines", lines, "invoice_id", invoice_ids, "freight_invoices")
        self._check_fk("audit_exceptions", exceptions, "invoice_id", invoice_ids, "freight_invoices")
        self._check_fk("credit_notes", credit_notes, "invoice_id", invoice_ids, "freight_invoices")
        self._check_fk("credit_notes", credit_notes, "exception_id", exception_ids, "audit_exceptions")

        # Check Invoices -> Shipments (Distinguishing expected injected anomalies)
        gt_anomalies = {gt["invoice_id"]: gt["anomaly_type"] for gt in ground_truth if gt.get("is_anomaly") == "True"}
        for inv in invoices:
            self.summary["checks_performed"] += 1
            if inv["shipment_id"] not in shipment_ids:
                if gt_anomalies.get(inv["invoice_id"]) == "UNKNOWN_SHIPMENT":
                    self.summary["injected_anomalies_confirmed"] += 1
                else:
                    self._add_issue("FK_VIOLATION", f"Invoice {inv['invoice_id']} has unknown shipment {inv['shipment_id']} not registered in ground truth.")

        # 3. Enum Validation
        self._check_enums("carriers", carriers, "mode", {e.value for e in CarrierMode})
        self._check_enums("carriers", carriers, "status", {e.value for e in CarrierStatus})
        self._check_enums("rate_cards", rate_cards, "service_level", {e.value for e in ServiceLevel})
        self._check_enums("rate_cards", rate_cards, "status", {e.value for e in RateCardStatus})
        self._check_enums("shipments", shipments, "service_level", {e.value for e in ServiceLevel})
        self._check_enums("shipments", shipments, "status", {e.value for e in ShipmentStatus})
        self._check_enums("weight_measurements", measurements, "weighed_by", {e.value for e in WeighedBy})
        self._check_enums("freight_invoices", invoices, "audit_status", {e.value for e in InvoiceAuditStatus})
        self._check_enums("invoice_lines", lines, "line_type", {e.value for e in InvoiceLineType})
        self._check_enums("audit_exceptions", exceptions, "exception_code", {e.value for e in ExceptionCode})
        self._check_enums("audit_exceptions", exceptions, "severity", {e.value for e in ExceptionSeverity})
        self._check_enums("credit_notes", credit_notes, "reconciliation_status", {e.value for e in CreditReconciliationStatus})

        # 4. Chronological Date Ordering
        for s in shipments:
            self.summary["checks_performed"] += 1
            s_date = datetime.date.fromisoformat(s["shipment_date"])
            if s.get("delivery_date"):
                d_date = datetime.date.fromisoformat(s["delivery_date"])
                if d_date < s_date:
                    self._add_issue("DATE_ORDERING", f"Shipment {s['shipment_id']} delivery_date {d_date} is before shipment_date {s_date}")

        for inv in invoices:
            self.summary["checks_performed"] += 1
            inv_date = datetime.date.fromisoformat(inv["invoice_date"])
            due_date = datetime.date.fromisoformat(inv["due_date"])
            if due_date < inv_date:
                self._add_issue("DATE_ORDERING", f"Invoice {inv['invoice_id']} due_date {due_date} is before invoice_date {inv_date}")

        # 5. Arithmetic Reconciliation
        # Line sum equals invoice total billed
        lines_by_inv: Dict[str, List[Dict[str, str]]] = {}
        for l in lines:
            inv_id = l["invoice_id"]
            if inv_id not in lines_by_inv:
                lines_by_inv[inv_id] = []
            lines_by_inv[inv_id].append(l)

        for inv in invoices:
            self.summary["checks_performed"] += 1
            inv_lines = lines_by_inv.get(inv["invoice_id"], [])
            calculated_sum = round(sum(float(l["billed_amount_usd"]) for l in inv_lines), 2)
            total_billed = round(float(inv["total_billed_usd"]), 2)
            if abs(calculated_sum - total_billed) > 0.02:
                self._add_issue("ARITHMETIC_MISMATCH", f"Invoice {inv['invoice_id']} billed total ${total_billed:.2f} != sum of lines ${calculated_sum:.2f}")

            # Variance reconciliation
            expected = round(float(inv["total_expected_usd"]), 2)
            variance = round(float(inv["variance_usd"]), 2)
            if abs((total_billed - expected) - variance) > 0.02:
                self._add_issue("ARITHMETIC_MISMATCH", f"Invoice {inv['invoice_id']} variance ${variance:.2f} != total_billed - total_expected (${(total_billed - expected):.2f})")

        # Weight measurement dimensional calculation check
        for wm in measurements:
            self.summary["checks_performed"] += 1
            l = float(wm["length_in"])
            w = float(wm["width_in"])
            h = float(wm["height_in"])
            scale_wt = float(wm["scale_weight_lbs"])
            expected_dim = round((l * w * h) / 139.0, 2)
            recorded_dim = round(float(wm["dim_weight_lbs"]), 2)
            expected_billable = max(scale_wt, expected_dim)
            recorded_billable = round(float(wm["billable_weight_lbs"]), 2)

            if abs(expected_dim - recorded_dim) > 0.05:
                self._add_issue("DIM_WEIGHT_MISCALCULATION", f"Measurement {wm['measurement_id']} dim weight mismatch: recorded {recorded_dim} vs calculated {expected_dim}")
            if abs(expected_billable - recorded_billable) > 0.05:
                self._add_issue("BILLABLE_WEIGHT_MISCALCULATION", f"Measurement {wm['measurement_id']} billable weight mismatch: recorded {recorded_billable} vs calculated {expected_billable}")

        # 6. Credit Note Reconciliation checks
        ex_map = {e["exception_id"]: float(e["disputed_amount_usd"]) for e in exceptions}
        for cr in credit_notes:
            self.summary["checks_performed"] += 1
            ex_amt = ex_map.get(cr["exception_id"], 0.0)
            cr_amt = float(cr["credit_amount_usd"])
            status = cr["reconciliation_status"]
            if cr_amt > ex_amt and status != "OVER_CREDITED":
                self._add_issue("CREDIT_RECONCILIATION", f"Credit note {cr['credit_note_id']} credit ${cr_amt} exceeds exception ${ex_amt} but status is {status}")
            elif cr_amt <= ex_amt and status == "OVER_CREDITED":
                self._add_issue("CREDIT_RECONCILIATION", f"Credit note {cr['credit_note_id']} marked OVER_CREDITED but credit ${cr_amt} <= exception ${ex_amt}")

        self.summary["checks_passed"] = self.summary["checks_performed"] - len(self.issues)
        self.summary["violations_found"] = len(self.issues)
        self.summary["validation_passed"] = (len(self.issues) == 0)

        return {
            "summary": self.summary,
            "issues": self.issues
        }

    def _check_pk_uniqueness(self, table: str, records: List[Dict[str, str]], pk_col: str):
        seen: Set[str] = set()
        for r in records:
            self.summary["checks_performed"] += 1
            val = r.get(pk_col)
            if not val or val in seen:
                self._add_issue("PK_DUPLICATE", f"Duplicate or null primary key '{val}' in table '{table}'.")
            seen.add(val)

    def _check_fk(self, table: str, records: List[Dict[str, str]], fk_col: str, parent_set: Set[str], parent_table: str):
        for r in records:
            self.summary["checks_performed"] += 1
            val = r.get(fk_col)
            if val and val not in parent_set:
                self._add_issue("FK_VIOLATION", f"Foreign key '{fk_col}' value '{val}' in table '{table}' not found in '{parent_table}'.")

    def _check_enums(self, table: str, records: List[Dict[str, str]], col: str, allowed: Set[str]):
        for r in records:
            self.summary["checks_performed"] += 1
            val = r.get(col)
            if val not in allowed:
                self._add_issue("INVALID_ENUM", f"Invalid value '{val}' for enum column '{col}' in table '{table}'. Allowed: {allowed}")

    def _add_issue(self, error_type: str, message: str):
        self.issues.append({"type": error_type, "message": message})

if __name__ == "__main__":
    validator = DataValidator()
    results = validator.validate_all()
    print("=== DATA VALIDATION SUMMARY ===")
    print(json.dumps(results["summary"], indent=2))
    if results["issues"]:
        print(f"\nIssues Found ({len(results['issues'])}):")
        for iss in results["issues"][:10]:
            print(f"  [{iss['type']}] {iss['message']}")
    else:
        print("\nAll data integrity and arithmetic checks PASSED successfully!")

