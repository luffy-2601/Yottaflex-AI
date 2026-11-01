"""
Unit tests for API Endpoints and Business Logic.
"""
import pytest
from api import (
    root, health_check, get_executive_metrics, get_carrier_scorecard, get_dispute_memo,
    audit_single_invoice, SingleInvoiceAuditRequest, AuditRequestLine,
    get_auth_provider_status, initiate_oauth_login, register_user, login_user, get_current_user, logout_user,
    EmailRegisterRequest, EmailLoginRequest
)

def test_root_endpoint():
    """Verify root endpoint returns welcome info and docs link."""
    res = root()
    assert res["version"] == "2.0.0"
    assert res["documentation"] == "/docs"

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

def test_api_auth_status_endpoint():
    """Verify auth status endpoint reports provider statuses."""
    status_res = get_auth_provider_status()
    assert "google" in status_res
    assert "github" in status_res
    assert "facebook" in status_res
    assert "x" in status_res
    assert status_res["database"] == "sqlite_connected"

def test_api_oauth_login_initiation():
    """Verify OAuth initiation returns correct authorization URLs."""
    for provider in ["google", "github", "facebook", "x"]:
        res = initiate_oauth_login(provider)
        assert res["provider"] == provider
        assert "authorization_url" in res
        assert "state" in res
        assert len(res["state"]) >= 32

def test_api_email_register_and_login_flow():
    """Verify REST API registration and login flow with session token."""
    test_email = "api_auditor@freightguard.io"
    try:
        reg_res = register_user(EmailRegisterRequest(
            name="API Auditor",
            email=test_email,
            password="FreightApiSecret@2026",
            role="Enterprise Auditor"
        ))
        assert reg_res["success"] is True
        assert reg_res["session_id"] is not None
        session_id = reg_res["session_id"]
    except Exception:
        # If user already exists
        login_res = login_user(EmailLoginRequest(
            email=test_email,
            password="FreightApiSecret@2026"
        ))
        assert login_res["success"] is True
        session_id = login_res["session_id"]

    # Verify session retrieval via /auth/me
    user_me = get_current_user(session_token=session_id)
    assert user_me["email"] == test_email
    assert "linked_accounts" in user_me

    # Verify logout
    logout_res = logout_user(session_token=session_id)
    assert logout_res["success"] is True
