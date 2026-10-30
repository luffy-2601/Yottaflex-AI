"""
Unit tests for Carrier Billing Integrity Scoring and Risk Profiling.
"""
import pytest
from src.analytics import CarrierRiskEngine

def test_carrier_risk_engine_calculation():
    """Verify carrier integrity scoring algorithm logic."""
    invoices = [
        {"invoice_id": "INV-01", "carrier_id": "CAR-01", "total_billed_usd": 1000.0, "audit_decision": "CLEAN"},
        {"invoice_id": "INV-02", "carrier_id": "CAR-01", "total_billed_usd": 1000.0, "audit_decision": "CLEAN"},
        {"invoice_id": "INV-03", "carrier_id": "CAR-02", "total_billed_usd": 1000.0, "audit_decision": "DISPUTE"},
        {"invoice_id": "INV-04", "carrier_id": "CAR-02", "total_billed_usd": 1000.0, "audit_decision": "DISPUTE"},
    ]
    exceptions = [
        {"invoice_id": "INV-03", "exception_code": "WEIGHT_TIER_MISMATCH", "disputed_amount_usd": 250.0},
        {"invoice_id": "INV-04", "exception_code": "WEIGHT_TIER_MISMATCH", "disputed_amount_usd": 300.0},
    ]

    engine = CarrierRiskEngine(invoices, exceptions)
    scorecards = engine.compute_carrier_scorecards()

    # CAR-01 should have perfect integrity score 100
    car1 = next(s for s in scorecards if s["carrier_id"] == "CAR-01")
    assert car1["integrity_score"] == 100.0
    assert car1["risk_tier"] == "TIER_1_TRUSTED"

    # CAR-02 should be penalized
    car2 = next(s for s in scorecards if s["carrier_id"] == "CAR-02")
    assert car2["integrity_score"] < 50.0
    assert car2["risk_tier"] == "TIER_3_HIGH_RISK"
    assert "WEIGHT_TIER_MISMATCH" in car2["primary_anomaly_pattern"]

