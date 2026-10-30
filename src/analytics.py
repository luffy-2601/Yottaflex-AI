"""
Carrier Billing Integrity Scoring (CBIS) and Anomaly Attribution Engine.
Computes multi-dimensional risk scores (0-100) for logistics service providers:
- Dispute frequency (% of invoices flagged)
- Financial overcharge dollar severity ratio
- Systematic failure pattern detection (e.g. chronic weight creep, tariff drift)
- Risk tiering: Tier 1 (Trusted), Tier 2 (Watchlist), Tier 3 (High-Risk Audit Hold)
"""
from typing import Dict, List, Any
import datetime

class CarrierRiskEngine:
    def __init__(self, invoices: List[Dict[str, Any]], exceptions: List[Dict[str, Any]]):
        self.invoices = invoices
        self.exceptions = exceptions

    def compute_carrier_scorecards(self) -> List[Dict[str, Any]]:
        """Compute comprehensive compliance scorecards for all active carriers."""
        carrier_stats: Dict[str, Dict[str, Any]] = {}
        invoices_map = {inv["invoice_id"]: inv for inv in self.invoices}

        # Aggregate invoice spend and counts
        for inv in self.invoices:
            cid = inv["carrier_id"]
            if cid not in carrier_stats:
                carrier_stats[cid] = {
                    "carrier_id": cid,
                    "total_invoices": 0,
                    "clean_invoices": 0,
                    "disputed_invoices": 0,
                    "total_billed_usd": 0.0,
                    "total_disputed_usd": 0.0,
                    "exception_types": {}
                }
            
            c = carrier_stats[cid]
            c["total_invoices"] += 1
            c["total_billed_usd"] += float(inv["total_billed_usd"])
            if inv.get("audit_decision") == "DISPUTE":
                c["disputed_invoices"] += 1
            else:
                c["clean_invoices"] += 1

        # Aggregate exception specifics (O(1) dictionary lookup)
        for ex in self.exceptions:
            inv_id = ex["invoice_id"]
            matched_inv = invoices_map.get(inv_id)
            if matched_inv:
                cid = matched_inv["carrier_id"]
                c = carrier_stats[cid]
                amt = float(ex["disputed_amount_usd"])
                c["total_disputed_usd"] += amt
                code = ex["exception_code"]
                c["exception_types"][code] = c["exception_types"].get(code, 0) + 1

        scorecards = []
        for cid, data in carrier_stats.items():
            tot_inv = data["total_invoices"]
            disp_inv = data["disputed_invoices"]
            tot_billed = data["total_billed_usd"]
            tot_disp = data["total_disputed_usd"]

            error_rate = disp_inv / tot_inv if tot_inv > 0 else 0.0
            overcharge_ratio = tot_disp / tot_billed if tot_billed > 0 else 0.0

            # Compute Carrier Billing Integrity Score (0 to 100)
            # 100 is perfect compliance; penalized by error rate and overcharge severity
            penalty = (error_rate * 55.0) + (min(1.0, overcharge_ratio * 4.0) * 45.0)
            integrity_score = round(max(0.0, 100.0 - penalty), 1)

            # Assign Risk Tier
            if integrity_score >= 85.0:
                risk_tier = "TIER_1_TRUSTED"
                action = "Auto-Approval & Sampling Audit"
            elif integrity_score >= 65.0:
                risk_tier = "TIER_2_WATCHLIST"
                action = "Enhanced Line-Item Pre-Payment Audit"
            else:
                risk_tier = "TIER_3_HIGH_RISK"
                action = "100% Mandatory Pre-Payment Hold & Dispute"

            # Primary Systematic Anomaly Pattern
            primary_pattern = "None (High Compliance)"
            if data["exception_types"]:
                top_code = max(data["exception_types"].items(), key=lambda x: x[1])
                primary_pattern = f"Systematic {top_code[0]} ({top_code[1]} occurrences)"

            scorecards.append({
                "carrier_id": cid,
                "integrity_score": integrity_score,
                "risk_tier": risk_tier,
                "recommended_action": action,
                "total_invoices": tot_inv,
                "clean_invoices": data["clean_invoices"],
                "disputed_invoices": disp_inv,
                "dispute_rate_pct": round(error_rate * 100, 2),
                "total_billed_usd": round(tot_billed, 2),
                "total_disputed_usd": round(tot_disp, 2),
                "primary_anomaly_pattern": primary_pattern,
                "exception_breakdown": data["exception_types"]
            })

        # Rank by integrity score ascending (highest risk first)
        scorecards.sort(key=lambda x: x["integrity_score"])
        return scorecards
