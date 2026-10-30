"""
Unit tests for Data Integrity Validator (Step 8).
"""
import pytest
from src.validator import DataValidator
from src.generator import FreightDataGenerator

@pytest.fixture(scope="module")
def validated_data(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("val_test_data")
    gen = FreightDataGenerator(seed=20261022, scale="starter")
    gen.generate_all()
    gen.export_all(tmp_dir)
    
    val = DataValidator(data_dir=tmp_dir)
    res = val.validate_all()
    return res

def test_validator_passes_all_checks(validated_data):
    """Integrity checks must pass with zero violations."""
    summary = validated_data["summary"]
    assert summary["validation_passed"] is True
    assert summary["violations_found"] == 0
    assert summary["checks_passed"] > 1000
