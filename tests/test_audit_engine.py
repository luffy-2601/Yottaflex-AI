"""
Unit and integration tests for Freight Audit Engine edge cases.
"""
import pytest
from src.audit_engine import FreightAuditEngine
from src.evaluation import AuditEvaluator
from src.generator import FreightDataGenerator

@pytest.fixture(scope="module")
def audit_data(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("audit_test_data")
    gen = FreightDataGenerator(seed=20261022, scale="starter")
    gen.generate_all()
    gen.export_all(tmp_dir)
    
    engine = FreightAuditEngine(data_dir=tmp_dir)
    results = engine.audit_all()
    
    evaluator = AuditEvaluator(data_dir=tmp_dir)
    eval_metrics = evaluator.evaluate(results["audit_results"])
    
    return {
        "engine": engine,
        "results": results,
        "eval_metrics": eval_metrics
    }

def test_unknown_shipment_detection(audit_data):
    """Edge Case 1: Invoices referencing non-existent shipments must be disputed with CRITICAL severity."""
    exceptions = audit_data["results"]["exceptions"]
    unknown_exs = [e for e in exceptions if e["exception_code"] == "UNKNOWN_SHIPMENT"]
    assert len(unknown_exs) > 0
    for ex in unknown_exs:
        assert ex["severity"] == "CRITICAL"
        assert ex["disputed_amount_usd"] > 0

def test_expired_rate_card_detection(audit_data):
    """Edge Case 2: Billing against an expired rate card must be flagged."""
    exceptions = audit_data["results"]["exceptions"]
    expired_exs = [e for e in exceptions if e["exception_code"] == "EXPIRED_RATE_CARD"]
    assert len(expired_exs) > 0
    for ex in expired_exs:
        assert ex["severity"] == "HIGH"
        assert "expired" in ex["explanation"].lower()

def test_weight_tier_misapplication_detection(audit_data):
    """Edge Case 3: Weight tier misapplication must be detected with variance calculated."""
    exceptions = audit_data["results"]["exceptions"]
    tier_exs = [e for e in exceptions if e["exception_code"] == "WEIGHT_TIER_MISMATCH"]
    assert len(tier_exs) > 0
    for ex in tier_exs:
        assert ex["disputed_amount_usd"] > 0

def test_duplicate_surcharge_detection(audit_data):
    """Edge Case 4: Redundant fuel surcharge lines on a single invoice must be detected."""
    exceptions = audit_data["results"]["exceptions"]
    dup_fsc_exs = [e for e in exceptions if e["exception_code"] == "DUPLICATE_SURCHARGE"]
    assert len(dup_fsc_exs) > 0
    for ex in dup_fsc_exs:
        assert "duplicate" in ex["explanation"].lower()

def test_credit_note_over_exception(audit_data):
    """Edge Case 5: Credit notes exceeding the dispute amount must be flagged as OVER_CREDITED."""
    credit_recs = audit_data["results"]["credit_reconciliation"]
    over_credited = [c for c in credit_recs if c["status"] == "OVER_CREDITED"]
    assert len(over_credited) > 0
    for c in over_credited:
        assert c["credit_amount_usd"] > c["disputed_amount_usd"]

def test_audit_evaluation_metrics(audit_data):
    """Verify precision and recall on the evaluation harness."""
    metrics = audit_data["eval_metrics"]["evaluation_metrics"]
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0

