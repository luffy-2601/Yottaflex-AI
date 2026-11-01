"""
Enterprise REST API Microservice for Freight Invoice Audit Platform (FastAPI).
Exposes production REST endpoints for:
- Live invoice re-rating and exception classification
- Carrier billing integrity scorecards
- Executive financial metrics
- Formal dispute memo generation
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# Ensure root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, status, Query, Response, Cookie
from src.config import DATA_DIR
from src.audit_engine import FreightAuditEngine
from src.evaluation import AuditEvaluator
from src.analytics import CarrierRiskEngine
from src.dispute_memo import DisputeMemoGenerator
from src.auth import (
    UserManager, GoogleOAuthProvider, GitHubOAuthProvider, FacebookOAuthProvider, TwitterOAuthProvider,
    generate_csrf_state, generate_pkce_pair
)

app = FastAPI(
    title="Freight Invoice Audit & Recovery REST API",
    description="Production-grade AI & Algorithmic Freight Audit Service. Validates carrier invoices against contracted tariffs, dimensions, and delivery records.",
    version="2.0.0"
)

# Load shared audit state on startup
engine = FreightAuditEngine(data_dir=DATA_DIR)
audit_cache: Dict[str, Any] = {}

def get_audit_data():
    if not audit_cache:
        csv_file = DATA_DIR / "freight_invoices.csv"
        if not csv_file.exists():
            from src.generator import SyntheticDataGenerator
            SyntheticDataGenerator(scale="starter").generate_all()

        audit_output = engine.audit_all()
        evaluator = AuditEvaluator(data_dir=DATA_DIR)
        eval_results = evaluator.evaluate(audit_output["audit_results"])
        
        risk_engine = CarrierRiskEngine(audit_output["audit_results"], audit_output["exceptions"])
        scorecards = risk_engine.compute_carrier_scorecards()
        
        audit_cache["output"] = audit_output
        audit_cache["eval"] = eval_results
        audit_cache["scorecards"] = scorecards
        audit_cache["invoices_map"] = {i["invoice_id"]: i for i in audit_output["audit_results"]}
        audit_cache["exceptions_map"] = {}
        for ex in audit_output["exceptions"]:
            audit_cache["exceptions_map"].setdefault(ex["invoice_id"], []).append(ex)
            
    return audit_cache

# ==========================================
# Pydantic Request / Response Schemas
# ==========================================

class AuditRequestLine(BaseModel):
    line_number: int
    line_type: str = Field(..., description="BASE_FREIGHT, FUEL_SURCHARGE, ACCESSORIAL")
    charge_code: str
    billed_rate: float
    billed_quantity: float
    billed_amount_usd: float

class SingleInvoiceAuditRequest(BaseModel):
    invoice_id: str
    carrier_id: str
    shipment_id: str
    invoice_date: str
    lines: List[AuditRequestLine]

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    engine: str

class EmailRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "Lead Freight Auditor"

class EmailLoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

# ==========================================
# REST API Endpoints
# ==========================================

# Temporary in-memory state store for CSRF state validation and PKCE verification
oauth_flow_cache: Dict[str, Dict[str, str]] = {}

@app.get("/auth/status", tags=["Authentication"])
def get_auth_provider_status():
    """Returns configuration status for all 4 OAuth providers."""
    return {
        "google": GoogleOAuthProvider.is_configured(),
        "github": GitHubOAuthProvider.is_configured(),
        "facebook": FacebookOAuthProvider.is_configured(),
        "x": TwitterOAuthProvider.is_configured(),
        "database": "sqlite_connected"
    }

@app.get("/auth/{provider}/login", tags=["Authentication"])
def initiate_oauth_login(provider: str, redirect_uri: Optional[str] = None):
    """Generates the official OAuth authorization URL for Google, GitHub, Facebook, or X."""
    p = provider.lower()
    state = generate_csrf_state()
    base_cb = redirect_uri or f"http://127.0.0.1:8000/auth/{p}/callback"

    if p == "google":
        auth_url = GoogleOAuthProvider.get_authorization_url(base_cb, state)
        oauth_flow_cache[state] = {"provider": "google", "redirect_uri": base_cb}
    elif p == "github":
        auth_url = GitHubOAuthProvider.get_authorization_url(base_cb, state)
        oauth_flow_cache[state] = {"provider": "github", "redirect_uri": base_cb}
    elif p == "facebook":
        auth_url = FacebookOAuthProvider.get_authorization_url(base_cb, state)
        oauth_flow_cache[state] = {"provider": "facebook", "redirect_uri": base_cb}
    elif p == "x":
        verifier, challenge = generate_pkce_pair()
        auth_url = TwitterOAuthProvider.get_authorization_url(base_cb, state, challenge)
        oauth_flow_cache[state] = {"provider": "x", "redirect_uri": base_cb, "code_verifier": verifier}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    configured_map = {
        "google": GoogleOAuthProvider.is_configured(),
        "github": GitHubOAuthProvider.is_configured(),
        "facebook": FacebookOAuthProvider.is_configured(),
        "x": TwitterOAuthProvider.is_configured()
    }

    return {
        "provider": p,
        "authorization_url": auth_url,
        "state": state,
        "configured": configured_map.get(p, False)
    }

@app.get("/auth/{provider}/callback", tags=["Authentication"])
def oauth_callback(provider: str, code: str = Query(...), state: str = Query(...)):
    """Receives provider authorization code, exchanges it on backend, verifies user, and creates session."""
    p = provider.lower()
    cached = oauth_flow_cache.pop(state, None)
    if not cached or cached.get("provider") != p:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state token (CSRF validation failed).")

    cb_uri = cached["redirect_uri"]

    if p == "google":
        token_res = GoogleOAuthProvider.exchange_code(code, cb_uri)
        if "error" in token_res:
            raise HTTPException(status_code=400, detail=token_res)
        profile = GoogleOAuthProvider.get_user_profile(token_res["access_token"])
    elif p == "github":
        token_res = GitHubOAuthProvider.exchange_code(code, cb_uri)
        if "error" in token_res:
            raise HTTPException(status_code=400, detail=token_res)
        profile = GitHubOAuthProvider.get_user_profile(token_res["access_token"])
    elif p == "facebook":
        token_res = FacebookOAuthProvider.exchange_code(code, cb_uri)
        if "error" in token_res:
            raise HTTPException(status_code=400, detail=token_res)
        profile = FacebookOAuthProvider.get_user_profile(token_res["access_token"])
    elif p == "x":
        token_res = TwitterOAuthProvider.exchange_code(code, cb_uri, cached["code_verifier"])
        if "error" in token_res:
            raise HTTPException(status_code=400, detail=token_res)
        profile = TwitterOAuthProvider.get_user_profile(token_res["access_token"])
    else:
        raise HTTPException(status_code=400, detail="Unknown provider")

    user = UserManager.get_or_create_oauth_user(
        provider=profile["provider"],
        provider_account_id=profile["provider_account_id"],
        email=profile["email"],
        name=profile["name"],
        profile_image=profile.get("profile_image"),
        email_verified=profile.get("email_verified", True)
    )
    session_id = UserManager.create_session(user["id"])
    return {
        "success": True,
        "message": f"Successfully authenticated via {provider.capitalize()}.",
        "user": user,
        "session_id": session_id
    }

@app.post("/auth/register", response_model=AuthResponse, tags=["Authentication"])
def register_user(req: EmailRegisterRequest):
    """Registers a new user with email and hashed password."""
    success, msg, user = UserManager.register_email_user(req.name, req.email, req.password, req.role or "Lead Freight Auditor")
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    session_id = UserManager.create_session(user["id"])
    return {"success": True, "message": msg, "user": user, "session_id": session_id}

@app.post("/auth/login", response_model=AuthResponse, tags=["Authentication"])
def login_user(req: EmailLoginRequest):
    """Authenticates an existing user via email and password."""
    success, msg, user = UserManager.authenticate_email_user(req.email, req.password)
    if not success:
        raise HTTPException(status_code=401, detail=msg)
    session_id = UserManager.create_session(user["id"])
    return {"success": True, "message": msg, "user": user, "session_id": session_id}

@app.get("/auth/me", tags=["Authentication"])
def get_current_user(session_token: Optional[str] = Cookie(None)):
    """Retrieves current user profile and linked accounts from session token."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated. Provide session_token cookie or header.")
    user = UserManager.validate_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")
    user["linked_accounts"] = UserManager.get_linked_accounts(user["id"])
    return user

@app.post("/auth/logout", tags=["Authentication"])
def logout_user(session_token: Optional[str] = Cookie(None)):
    """Logs out and deletes the session token."""
    if session_token:
        UserManager.delete_session(session_token)
    return {"success": True, "message": "Successfully logged out."}

@app.get("/", tags=["Root"])
def root():
    """Root endpoint welcoming visitors and directing to interactive OpenAPI documentation."""
    return {
        "service": "Freight Invoice Audit & Recovery REST API",
        "version": "2.0.0",
        "documentation": "/docs",
        "health": "/health",
        "description": "Production AI & Algorithmic Freight Audit Service. Open /docs for Swagger UI."
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "freight-audit-engine",
        "version": "2.0.0",
        "engine": "deterministic-rating-v2"
    }

@app.get("/api/v1/metrics/executive", tags=["Analytics & Reporting"])
def get_executive_metrics():
    """Retrieve executive financial summary and evaluation metrics."""
    data = get_audit_data()
    return {
        "financial_summary": data["output"]["summary"],
        "evaluation_performance": data["eval"]["evaluation_metrics"],
        "confusion_matrix": data["eval"]["confusion_matrix"],
        "anomaly_breakdown": data["eval"]["anomaly_detection_breakdown"]
    }

@app.get("/api/v1/carriers/{carrier_id}/scorecard", tags=["Carrier Integrity"])
def get_carrier_scorecard(carrier_id: str):
    """Retrieve Carrier Billing Integrity Score (CBIS) and risk profile."""
    data = get_audit_data()
    for sc in data["scorecards"]:
        if sc["carrier_id"].upper() == carrier_id.upper():
            return sc
    raise HTTPException(status_code=404, detail=f"Carrier '{carrier_id}' not found.")

@app.get("/api/v1/carriers/scorecards/all", tags=["Carrier Integrity"])
def get_all_scorecards(limit: int = 20):
    """List carrier risk scorecards ranked by highest dispute risk."""
    data = get_audit_data()
    return data["scorecards"][:limit]

@app.get("/api/v1/disputes/{invoice_id}/memo", tags=["Dispute Settlement"])
def get_dispute_memo(invoice_id: str):
    """Generate formal legal carrier dispute claim notice for an invoice."""
    data = get_audit_data()
    inv = data["invoices_map"].get(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found in audit ledger.")
    
    exs = data["exceptions_map"].get(invoice_id, [])
    lines = engine.invoice_lines.get(invoice_id, [])
    
    memo_text = DisputeMemoGenerator.generate_memo(inv, exs, lines)
    return {
        "invoice_id": invoice_id,
        "carrier_id": inv["carrier_id"],
        "dispute_verdict": inv["audit_decision"],
        "disputed_amount_usd": inv["variance_usd"],
        "formal_claim_memo": memo_text
    }

@app.post("/api/v1/audit/single", tags=["Audit Execution"])
def audit_single_invoice(payload: SingleInvoiceAuditRequest):
    """Real-time audit endpoint for streaming single invoice payloads."""
    # Check shipment registry
    if payload.shipment_id not in engine.shipments:
        total_billed = sum(l.billed_amount_usd for l in payload.lines)
        return {
            "invoice_id": payload.invoice_id,
            "audit_decision": "DISPUTE",
            "audit_status": "DISPUTED",
            "total_billed_usd": total_billed,
            "total_expected_usd": 0.0,
            "variance_usd": total_billed,
            "exceptions": [{
                "exception_code": "UNKNOWN_SHIPMENT",
                "severity": "CRITICAL",
                "disputed_amount_usd": total_billed,
                "explanation": f"Shipment '{payload.shipment_id}' does not exist in master logistics registry."
            }]
        }
    
    # Shipment found - retrieve characteristics
    shipment = engine.shipments[payload.shipment_id]
    wm = engine.weight_measurements.get(payload.shipment_id)
    billable_wt = float(wm["billable_weight_lbs"]) if wm else 500.0
    
    rate_card, rc_status = engine.find_contracted_rate_card(
        carrier_id=payload.carrier_id,
        lane_id=shipment["lane_id"],
        service=shipment["service_level"],
        weight=billable_wt,
        ship_date_str=shipment["shipment_date"]
    )
    
    cwt_units = round(billable_wt / 100.0, 2)
    contract_cwt = float(rate_card["rate_per_cwt_usd"]) if rate_card else 30.0
    contract_min = float(rate_card["min_charge_usd"]) if rate_card else 75.0
    contract_fuel_pct = float(rate_card["fuel_surcharge_percent"]) if rate_card else 0.20
    
    expected_base = max(contract_min, round(cwt_units * contract_cwt, 2))
    expected_fuel = round(expected_base * contract_fuel_pct, 2)
    
    exceptions = []
    total_expected = 0.0
    total_billed = round(sum(l.billed_amount_usd for l in payload.lines), 2)
    
    fsc_count = 0
    for l in payload.lines:
        line_exp = 0.0
        if l.line_type == "BASE_FREIGHT":
            line_exp = expected_base
            diff = round(l.billed_amount_usd - line_exp, 2)
            if diff > 1.0:
                exceptions.append({
                    "exception_code": "WEIGHT_TIER_MISMATCH",
                    "severity": "MEDIUM",
                    "disputed_amount_usd": diff,
                    "explanation": f"Billed base ${l.billed_amount_usd:.2f} exceeds contract tariff ${line_exp:.2f}."
                })
        elif l.line_type == "FUEL_SURCHARGE":
            fsc_count += 1
            if fsc_count > 1:
                exceptions.append({
                    "exception_code": "DUPLICATE_SURCHARGE",
                    "severity": "HIGH",
                    "disputed_amount_usd": l.billed_amount_usd,
                    "explanation": f"Duplicate fuel surcharge line billed: ${l.billed_amount_usd:.2f}."
                })
            else:
                line_exp = expected_fuel
        total_expected += line_exp
        
    variance = round(total_billed - total_expected, 2)
    decision = "CLEAN" if len(exceptions) == 0 and abs(variance) <= 0.05 else "DISPUTE"
    
    return {
        "invoice_id": payload.invoice_id,
        "carrier_id": payload.carrier_id,
        "shipment_id": payload.shipment_id,
        "audit_decision": decision,
        "total_billed_usd": total_billed,
        "total_expected_usd": round(total_expected, 2),
        "variance_usd": variance,
        "exceptions": exceptions
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)

