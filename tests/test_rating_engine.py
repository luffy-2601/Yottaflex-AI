"""
Unit tests for Freight Rating Mechanics and Contract Tariffs.
"""
import pytest
from src.schema import RateCard, ServiceLevel, RateCardStatus
from src.config import ACCESSORIAL_RATES, DIM_FACTORS

def test_dim_weight_factors():
    """Verify standard dimensional weight calculation against standard divisors 139 and 166."""
    length, width, height = 48.0, 40.0, 48.0
    volume_cu_in = length * width * height # 92,160 cu in
    
    dim_139 = round(volume_cu_in / 139.0, 2)
    dim_166 = round(volume_cu_in / 166.0, 2)
    
    assert dim_139 == 663.02
    assert dim_166 == 555.18

def test_hundredweight_rating_formula():
    """Verify base freight formula with hundredweight rounding."""
    billable_weight = 1250.75 # lbs
    cwt_units = round(billable_weight / 100.0, 2) # 12.51 cwt
    rate_per_cwt = 32.50
    min_charge = 85.00
    
    calculated_base = round(cwt_units * rate_per_cwt, 2)
    final_base = max(min_charge, calculated_base)
    
    assert cwt_units == 12.51
    assert calculated_base == 406.57
    assert final_base == 406.57

def test_minimum_charge_enforcement():
    """Verify minimum charge threshold applies when weight charge is lower."""
    billable_weight = 75.0 # lbs (lightweight package)
    cwt_units = round(billable_weight / 100.0, 2) # 0.75 cwt
    rate_per_cwt = 40.00
    min_charge = 95.00
    
    calculated_base = round(cwt_units * rate_per_cwt, 2) # $30.00
    final_base = max(min_charge, calculated_base)
    
    assert calculated_base == 30.00
    assert final_base == 95.00 # Minimum charge enforced

def test_accessorial_standard_tariffs():
    """Verify contracted accessorial tariff schedule."""
    assert ACCESSORIAL_RATES["LIFTGATE"] == 75.00
    assert ACCESSORIAL_RATES["RESIDENTIAL"] == 65.00
    assert ACCESSORIAL_RATES["HAZMAT"] == 150.00
    assert ACCESSORIAL_RATES["DETENTION"] == 100.00
