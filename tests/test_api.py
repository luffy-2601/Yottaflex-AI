"""
Unit tests for API Endpoints and Business Logic.
"""
import pytest
from api import health_check, get_executive_metrics, get_carrier_scorecard, get_dispute_memo, audit_single_invoice, SingleInvoiceAuditRequest, AuditRequestLine

def test_health_endpoint():
    """Verify health endpoint returns healthy status."""
    res = health_check()
    assert res["status"] == "healthy"
    assert res["version"] == "2.0.0"

def test_executive_metrics_endpoint():
    """Verify executive financial metrics."""
    res = get_executive_metrics()
    assert "financial_summary" in res
    assert "evaluation_performance" in res
    assert res["evaluation_performance"]["precision"] == 1.0
    assert res["evaluation_performance"]["recall"] == 1.0

def test_carrier_scorecard_endpoint():
    """Verify carrier risk scorecards endpoint."""
    res = get_carrier_scorecard("CAR-000001")
    assert res["carrier_id"] == "CAR-000001"
    assert "integrity_score" in res
    assert "risk_tier" in res

def test_dispute_memo_endpoint():
    """Verify legal dispute claim memo generation endpoint."""
    res = get_dispute_memo("FINV-2026-000019")
    assert "formal_claim_memo" in res
    assert "FORMAL FREIGHT BILLING DISPUTE" in res["formal_claim_memo"]

def test_single_invoice_audit_endpoint_unknown_shipment():
    """Verify streaming single invoice audit correctly identifies unknown shipments."""
    req = SingleInvoiceAuditRequest(
        invoice_id="FINV-TEST-9999",
        carrier_id="CAR-000001",
        shipment_id="SHP-NON-EXISTENT",
        invoice_date="2026-06-01",
        lines=[AuditRequestLine(
            line_number=1,
            line_type="BASE_FREIGHT",
            charge_code="BASE",
            billed_rate=25.0,
            billed_quantity=5.0,
            billed_amount_usd=125.0
        )]
    )
    res = audit_single_invoice(req)
    assert res["audit_decision"] == "DISPUTE"
    assert res["exceptions"][0]["exception_code"] == "UNKNOWN_SHIPMENT"
