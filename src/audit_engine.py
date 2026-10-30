"""
Freight Invoice Audit and Decision Engine.
Implements the core business workflow:
- Shipment validation
- Duplicate invoice detection
- Re-rating against contracted rate cards (lane, service, weight tiers, dim weight)
- Fuel surcharge & accessorial verification against delivery records
- Line-level variance classification & exception generation
- Credit note dispute reconciliation
- Complete traceability and event history
"""
import csv
import datetime
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_DIR, ACCESSORIAL_RATES, ID_EXCEPTION_FMT
from src.schema import (
    ExceptionCode, ExceptionSeverity, ExceptionStatus,
    InvoiceAuditStatus, LineStatus, InvoiceLineType,
    CreditReconciliationStatus
)

class FreightAuditEngine:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.carriers: Dict[str, Dict[str, Any]] = {}
        self.lanes: Dict[str, Dict[str, Any]] = {}
        self.rate_cards: List[Dict[str, Any]] = []
        self.shipments: Dict[str, Dict[str, Any]] = {}
        self.shipment_legs: Dict[str, List[Dict[str, Any]]] = {}
        self.weight_measurements: Dict[str, Dict[str, Any]] = {}
        self.accessorials: Dict[str, List[Dict[str, Any]]] = {}
        self.invoices: List[Dict[str, Any]] = []
        self.invoice_lines: Dict[str, List[Dict[str, Any]]] = {}
        self.credit_notes: List[Dict[str, Any]] = []

        # Audit outputs
        self.audit_results: List[Dict[str, Any]] = []
        self.generated_exceptions: List[Dict[str, Any]] = []
        self.audit_events_history: List[Dict[str, Any]] = []
        self.reconciled_credit_notes: List[Dict[str, Any]] = []

    def load_data(self):
        """Load operational dataset from CSVs."""
        self.carriers = {r["carrier_id"]: r for r in self._read_csv("carriers.csv")}
        self.lanes = {r["lane_id"]: r for r in self._read_csv("lanes.csv")}
        self.rate_cards = self._read_csv("rate_cards.csv")
        self.rate_cards_lookup: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
        for rc in self.rate_cards:
            key = (rc["carrier_id"], rc["lane_id"], rc["service_level"])
            if key not in self.rate_cards_lookup:
                self.rate_cards_lookup[key] = []
            self.rate_cards_lookup[key].append(rc)

        self.shipments = {r["shipment_id"]: r for r in self._read_csv("shipments.csv")}
        
        for leg in self._read_csv("shipment_legs.csv"):
            shp_id = leg["shipment_id"]
            if shp_id not in self.shipment_legs:
                self.shipment_legs[shp_id] = []
            self.shipment_legs[shp_id].append(leg)

        for wm in self._read_csv("weight_measurements.csv"):
            self.weight_measurements[wm["shipment_id"]] = wm

        for acc in self._read_csv("accessorials.csv"):
            shp_id = acc["shipment_id"]
            if shp_id not in self.accessorials:
                self.accessorials[shp_id] = []
            self.accessorials[shp_id].append(acc)

        self.invoices = self._read_csv("freight_invoices.csv")
        
        for l in self._read_csv("invoice_lines.csv"):
            inv_id = l["invoice_id"]
            if inv_id not in self.invoice_lines:
                self.invoice_lines[inv_id] = []
            self.invoice_lines[inv_id].append(l)

        self.credit_notes = self._read_csv("credit_notes.csv")

    def _read_csv(self, filename: str) -> List[Dict[str, Any]]:
        path = self.data_dir / filename
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def find_contracted_rate_card(self, carrier_id: str, lane_id: str, service: str, weight: float, ship_date_str: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Query contracted rate cards for carrier, lane, service level, weight tier, and validity window.
        Returns (rate_card, status_reason).
        """
        ship_date = datetime.date.fromisoformat(ship_date_str)
        matching_cards = self.rate_cards_lookup.get((carrier_id, lane_id, service), [])

        if not matching_cards:
            return None, "NO_RATE_CARD_FOUND"

        # Check weight tier
        tier_matched = None
        for rc in matching_cards:
            min_wt = float(rc["weight_tier_min_lbs"])
            max_wt = float(rc["weight_tier_max_lbs"])
            if min_wt <= weight < max_wt:
                tier_matched = rc
                break

        if not tier_matched:
            return matching_cards[0], "TIER_OUT_OF_BOUNDS"

        # Check date validity
        eff_date = datetime.date.fromisoformat(tier_matched["effective_date"])
        exp_date = datetime.date.fromisoformat(tier_matched["expiration_date"])

        if tier_matched.get("status") == "EXPIRED" or ship_date < eff_date or ship_date > exp_date:
            return tier_matched, "EXPIRED_CARD"

        return tier_matched, "ACTIVE_VALID"

    def audit_all(self) -> Dict[str, Any]:
        """
        Execute end-to-end freight audit across all invoices.
        """
        self.load_data()
        exception_idx = 1
        processed_shipments: Dict[str, str] = {}  # shipment_id -> first invoice_id (duplicate check)

        total_invoices_audited = len(self.invoices)
        clean_invoices_count = 0
        disputed_invoices_count = 0
        total_billed_amount = 0.0
        total_expected_amount = 0.0
        total_disputed_amount = 0.0

        for inv in self.invoices:
            inv_id = inv["invoice_id"]
            carrier_id = inv["carrier_id"]
            shipment_id = inv["shipment_id"]
            inv_date = inv["invoice_date"]
            lines = self.invoice_lines.get(inv_id, [])

            total_billed = round(float(inv["total_billed_usd"]), 2)
            total_billed_amount += total_billed

            invoice_exceptions: List[Dict[str, Any]] = []
            invoice_expected_total = 0.0

            # -------------------------------------------------------------
            # Check 1: Shipment Registry Verification
            # -------------------------------------------------------------
            if shipment_id not in self.shipments:
                ex_id = ID_EXCEPTION_FMT.format(exception_idx)
                exception_idx += 1
                ex = {
                    "exception_id": ex_id,
                    "invoice_id": inv_id,
                    "line_id": lines[0]["line_id"] if lines else None,
                    "exception_code": ExceptionCode.UNKNOWN_SHIPMENT.value,
                    "severity": ExceptionSeverity.CRITICAL.value,
                    "disputed_amount_usd": total_billed,
                    "explanation": f"Shipment ID '{shipment_id}' does not exist in logistics shipment master table. Full invoice disputed.",
                    "status": ExceptionStatus.APPROVED_DISPUTE.value,
                    "created_at": f"{inv_date}T12:00:00Z"
                }
                invoice_exceptions.append(ex)
                total_expected = 0.00
                total_variance = total_billed

                # Record event
                self._record_event(inv_id, "AUDIT_VERDICT", "PENDING", "DISPUTED", ex["explanation"])
            
            else:
                shipment = self.shipments[shipment_id]

                # -------------------------------------------------------------
                # Check 2: Duplicate Invoice Verification
                # -------------------------------------------------------------
                if shipment_id in processed_shipments:
                    prior_inv = processed_shipments[shipment_id]
                    ex_id = ID_EXCEPTION_FMT.format(exception_idx)
                    exception_idx += 1
                    ex = {
                        "exception_id": ex_id,
                        "invoice_id": inv_id,
                        "line_id": lines[0]["line_id"] if lines else None,
                        "exception_code": ExceptionCode.DUPLICATE_INVOICE.value,
                        "severity": ExceptionSeverity.HIGH.value,
                        "disputed_amount_usd": total_billed,
                        "explanation": f"Duplicate invoice detected for shipment '{shipment_id}'. Previously billed under invoice '{prior_inv}'.",
                        "status": ExceptionStatus.APPROVED_DISPUTE.value,
                        "created_at": f"{inv_date}T12:00:00Z"
                    }
                    invoice_exceptions.append(ex)
                    total_expected = 0.00
                    total_variance = total_billed
                    self._record_event(inv_id, "AUDIT_VERDICT", "PENDING", "DISPUTED", ex["explanation"])

                else:
                    processed_shipments[shipment_id] = inv_id

                    # -------------------------------------------------------------
                    # Check 3: Rate Card Validity & Re-rating
                    # -------------------------------------------------------------
                    wm = self.weight_measurements.get(shipment_id)
                    billable_wt = float(wm["billable_weight_lbs"]) if wm else 500.0

                    rate_card, rc_status = self.find_contracted_rate_card(
                        carrier_id=carrier_id,
                        lane_id=shipment["lane_id"],
                        service=shipment["service_level"],
                        weight=billable_wt,
                        ship_date_str=shipment["shipment_date"]
                    )

                    # -------------------------------------------------------------
                    # Check 4: Line-by-Line Item Audit
                    # -------------------------------------------------------------
                    contract_cwt = float(rate_card["rate_per_cwt_usd"]) if rate_card else 30.0
                    contract_min = float(rate_card["min_charge_usd"]) if rate_card else 75.0
                    contract_fuel_pct = float(rate_card["fuel_surcharge_percent"]) if rate_card else 0.20
                    cwt_units = round(billable_wt / 100.0, 2)
                    expected_base_calc = max(contract_min, round(cwt_units * contract_cwt, 2))
                    expected_fuel_calc = round(expected_base_calc * contract_fuel_pct, 2)

                    # Track verified accessorials
                    ship_accs = self.accessorials.get(shipment_id, [])
                    authorized_codes = {a["service_code"]: float(a["contract_rate_usd"]) for a in ship_accs if a["authorized"] in ("1", 1, True, "True")}

                    seen_fsc_lines = 0

                    for line in lines:
                        l_type = line["line_type"]
                        billed_amt = float(line["billed_amount_usd"])
                        line_exp = 0.0

                        if l_type == InvoiceLineType.BASE_FREIGHT.value:
                            line_exp = expected_base_calc
                            variance = round(billed_amt - line_exp, 2)
                            
                            if variance > 1.00:
                                ex_id = ID_EXCEPTION_FMT.format(exception_idx)
                                exception_idx += 1
                                is_expired_sched = ("expired" in line["description"].lower() or rc_status == "EXPIRED_CARD")
                                ex_code = ExceptionCode.EXPIRED_RATE_CARD.value if is_expired_sched else ExceptionCode.WEIGHT_TIER_MISMATCH.value
                                ex_explanation = (
                                    f"Carrier billed under expired rate schedule. Billed ${billed_amt:.2f} vs active tariff ${line_exp:.2f}."
                                    if is_expired_sched else
                                    f"Base freight billed at ${billed_amt:.2f} exceeds contracted rate of ${line_exp:.2f} for billable weight {billable_wt} lbs."
                                )
                                ex = {
                                    "exception_id": ex_id,
                                    "invoice_id": inv_id,
                                    "line_id": line["line_id"],
                                    "exception_code": ex_code,
                                    "severity": ExceptionSeverity.HIGH.value if is_expired_sched else ExceptionSeverity.MEDIUM.value,
                                    "disputed_amount_usd": variance,
                                    "explanation": ex_explanation,
                                    "status": ExceptionStatus.APPROVED_DISPUTE.value,
                                    "created_at": f"{inv_date}T12:00:00Z"
                                }
                                invoice_exceptions.append(ex)

                        elif l_type == InvoiceLineType.FUEL_SURCHARGE.value:
                            seen_fsc_lines += 1
                            if seen_fsc_lines > 1 or line["charge_code"] == "FSC_DUP":
                                # Duplicate Surcharge Anomaly
                                line_exp = 0.00
                                ex_id = ID_EXCEPTION_FMT.format(exception_idx)
                                exception_idx += 1
                                ex = {
                                    "exception_id": ex_id,
                                    "invoice_id": inv_id,
                                    "line_id": line["line_id"],
                                    "exception_code": ExceptionCode.DUPLICATE_SURCHARGE.value,
                                    "severity": ExceptionSeverity.HIGH.value,
                                    "disputed_amount_usd": billed_amt,
                                    "explanation": f"Duplicate fuel surcharge line detected on single invoice: billed ${billed_amt:.2f}.",
                                    "status": ExceptionStatus.APPROVED_DISPUTE.value,
                                    "created_at": f"{inv_date}T12:00:00Z"
                                }
                                invoice_exceptions.append(ex)
                            else:
                                line_exp = expected_fuel_calc

                        elif l_type == InvoiceLineType.ACCESSORIAL.value:
                            code = line["charge_code"]
                            if code in authorized_codes:
                                line_exp = authorized_codes[code]
                            else:
                                # Unauthorized accessorial
                                line_exp = 0.00
                                ex_id = ID_EXCEPTION_FMT.format(exception_idx)
                                exception_idx += 1
                                ex = {
                                    "exception_id": ex_id,
                                    "invoice_id": inv_id,
                                    "line_id": line["line_id"],
                                    "exception_code": ExceptionCode.UNAUTHORIZED_ACCESSORIAL.value,
                                    "severity": ExceptionSeverity.MEDIUM.value,
                                    "disputed_amount_usd": billed_amt,
                                    "explanation": f"Accessorial charge '{code}' for ${billed_amt:.2f} was not authorized or documented on delivery receipt.",
                                    "status": ExceptionStatus.APPROVED_DISPUTE.value,
                                    "created_at": f"{inv_date}T12:00:00Z"
                                }
                                invoice_exceptions.append(ex)

                        invoice_expected_total += line_exp

                    total_expected = round(invoice_expected_total, 2)
                    total_variance = round(total_billed - total_expected, 2)

            # Determine final audit status
            is_clean = (len(invoice_exceptions) == 0 and abs(total_variance) <= 0.05)
            final_status = InvoiceAuditStatus.AUDITED_CLEAN.value if is_clean else InvoiceAuditStatus.DISPUTED.value

            if is_clean:
                clean_invoices_count += 1
                audit_decision = "CLEAN"
            else:
                disputed_invoices_count += 1
                audit_decision = "DISPUTE"
                disputed_amt_sum = sum(e["disputed_amount_usd"] for e in invoice_exceptions)
                total_disputed_amount += disputed_amt_sum

            total_expected_amount += total_expected

            self.audit_results.append({
                "invoice_id": inv_id,
                "carrier_id": carrier_id,
                "shipment_id": shipment_id,
                "total_billed_usd": total_billed,
                "total_expected_usd": total_expected,
                "variance_usd": total_variance,
                "audit_decision": audit_decision,
                "audit_status": final_status,
                "exceptions_count": len(invoice_exceptions),
                "exceptions": invoice_exceptions
            })

            self.generated_exceptions.extend(invoice_exceptions)

        # -------------------------------------------------------------
        # Check 5: Credit Note Reconciliation
        # -------------------------------------------------------------
        ex_dict = {e["exception_id"]: e for e in self.generated_exceptions}
        for cr in self.credit_notes:
            cr_id = cr["credit_note_id"]
            cr_amt = float(cr["credit_amount_usd"])
            ex_id = cr.get("exception_id")
            
            ex = ex_dict.get(ex_id)
            ex_disputed = float(ex["disputed_amount_usd"]) if ex else 0.0

            if cr_amt > ex_disputed:
                rec_status = CreditReconciliationStatus.OVER_CREDITED.value
                # Flag over-credit exception
                over_amt = round(cr_amt - ex_disputed, 2)
                self.reconciled_credit_notes.append({
                    "credit_note_id": cr_id,
                    "invoice_id": cr["invoice_id"],
                    "exception_id": ex_id,
                    "credit_amount_usd": cr_amt,
                    "disputed_amount_usd": ex_disputed,
                    "difference_usd": over_amt,
                    "status": rec_status,
                    "notes": f"Credit note amount (${cr_amt:.2f}) exceeds dispute amount (${ex_disputed:.2f}) by ${over_amt:.2f}."
                })
            else:
                rec_status = CreditReconciliationStatus.RECONCILED.value
                self.reconciled_credit_notes.append({
                    "credit_note_id": cr_id,
                    "invoice_id": cr["invoice_id"],
                    "exception_id": ex_id,
                    "credit_amount_usd": cr_amt,
                    "disputed_amount_usd": ex_disputed,
                    "difference_usd": 0.00,
                    "status": rec_status,
                    "notes": "Credit note fully reconciles approved exception dispute."
                })

        summary = {
            "total_invoices_audited": total_invoices_audited,
            "clean_invoices": clean_invoices_count,
            "disputed_invoices": disputed_invoices_count,
            "total_exceptions_raised": len(self.generated_exceptions),
            "total_billed_amount_usd": round(total_billed_amount, 2),
            "total_expected_amount_usd": round(total_expected_amount, 2),
            "total_disputed_amount_usd": round(total_disputed_amount, 2),
            "credit_notes_reconciled": len(self.reconciled_credit_notes),
            "credit_over_exception_count": sum(1 for c in self.reconciled_credit_notes if c["status"] == "OVER_CREDITED"),
            "audit_pass_rate": round(clean_invoices_count / total_invoices_audited, 4) if total_invoices_audited else 0.0
        }

        return {
            "summary": summary,
            "audit_results": self.audit_results,
            "exceptions": self.generated_exceptions,
            "credit_reconciliation": self.reconciled_credit_notes
        }

    def _record_event(self, invoice_id: str, event_type: str, old_state: str, new_state: str, notes: str):
        self.audit_events_history.append({
            "event_id": f"EVT-{len(self.audit_events_history) + 1:06d}",
            "invoice_id": invoice_id,
            "event_type": event_type,
            "old_state": old_state,
            "new_state": new_state,
            "actor": "AUTOMATED_AUDIT_ENGINE",
            "notes": notes,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

if __name__ == "__main__":
    engine = FreightAuditEngine()
    audit_output = engine.audit_all()
    print("=== FREIGHT AUDIT EXECUTION COMPLETED ===")
    print(json.dumps(audit_output["summary"], indent=2))
