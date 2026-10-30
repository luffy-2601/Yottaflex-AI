"""
Unit tests for Synthetic Data Generator and Mathematical Models.
"""
import pytest
import re
from src.config import DEFAULT_SEED
from src.generator import FreightDataGenerator

@pytest.fixture(scope="module")
def generator_instance():
    gen = FreightDataGenerator(seed=DEFAULT_SEED, scale="starter")
    gen.generate_all()
    return gen

def test_id_nomenclature(generator_instance):
    """Verify all entities conform to specified ID formats."""
    gen = generator_instance
    
    # Carrier: CAR-000001
    assert re.match(r"^CAR-\d{6}$", gen.carriers[0].carrier_id)
    
    # RateCard: RATE-CAR-000001-2026-0001
    assert re.match(r"^RATE-CAR-\d{6}-2026-\d{4}$", gen.rate_cards[0].rate_card_id)
    
    # Shipment: SHP-2026-000001
    assert re.match(r"^SHP-2026-\d{6}$", gen.shipments[0].shipment_id)
    
    # ShipmentLeg: LEG-SHP-2026-000001-01
    assert re.match(r"^LEG-SHP-2026-\d{6}-\d{2}$", gen.shipment_legs[0].leg_id)
    
    # WeightMeasurement: WM-SHP-2026-000001-01
    assert re.match(r"^WM-SHP-2026-\d{6}-\d{2}$", gen.weight_measurements[0].measurement_id)
    
    # Invoice: FINV-2026-000001
    assert re.match(r"^FINV-2026-\d{6}$", gen.freight_invoices[0].invoice_id)
    
    # InvoiceLine: FLINE-FINV-2026-000001-01
    assert re.match(r"^FLINE-FINV-2026-\d{6}-\d{2}$", gen.invoice_lines[0].line_id)
    
    # Exception: FEX-2026-000001
    assert re.match(r"^FEX-2026-\d{6}$", gen.audit_exceptions[0].exception_id)

def test_dimensional_weight_calculation(generator_instance):
    """Verify dimensional weight formula: (L * W * H) / 139."""
    gen = generator_instance
    for wm in gen.weight_measurements:
        expected_dim = round((wm.length_in * wm.width_in * wm.height_in) / 139.0, 2)
        assert abs(wm.dim_weight_lbs - expected_dim) <= 0.01
        assert wm.billable_weight_lbs == round(max(wm.scale_weight_lbs, wm.dim_weight_lbs), 2)

def test_line_totals_match_invoice(generator_instance):
    """Verify total billed on invoice equals sum of itemized lines."""
    gen = generator_instance
    lines_by_inv = {}
    for l in gen.invoice_lines:
        lines_by_inv.setdefault(l.invoice_id, []).append(l.billed_amount_usd)
        
    for inv in gen.freight_invoices:
        billed_lines = lines_by_inv.get(inv.invoice_id, [])
        assert abs(inv.total_billed_usd - round(sum(billed_lines), 2)) <= 0.01
