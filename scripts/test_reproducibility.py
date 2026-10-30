"""
Step 10: Deterministic Reproducibility Verification Harness.
Regenerates dataset twice with seed 20261022 into isolated directories,
computes SHA-256 hashes of every generated table, and asserts identical row counts and checksums.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_SEED
from src.generator import FreightDataGenerator

def compute_file_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def test_reproducibility(seed: int = DEFAULT_SEED, scale: str = "starter"):
    print("=================================================================")
    print(f"STEP 10: REPRODUCIBILITY VERIFICATION TEST (Seed={seed}, Scale={scale})")
    print("=================================================================")
    
    dir_run1 = PROJECT_ROOT / "data" / "repro_run1"
    dir_run2 = PROJECT_ROOT / "data" / "repro_run2"

    if dir_run1.exists():
        shutil.rmtree(dir_run1)
    if dir_run2.exists():
        shutil.rmtree(dir_run2)

    try:
        print("[Run 1/2] Generating first dataset...")
        gen1 = FreightDataGenerator(seed=seed, scale=scale)
        gen1.generate_all()
        manifest1 = gen1.export_all(dir_run1)

        print("[Run 2/2] Generating second dataset with identical seed...")
        gen2 = FreightDataGenerator(seed=seed, scale=scale)
        gen2.generate_all()
        manifest2 = gen2.export_all(dir_run2)

        print("\nVerifying SHA-256 checksums and row counts across all generated files:")
        print(f"{'Filename':<30} | {'Run 1 Rows':<10} | {'Run 2 Rows':<10} | {'Run 1 SHA-256 (Prefix)':<24} | {'Match?':<6}")
        print("-" * 92)

        files_to_check = [
            "carriers.csv",
            "lanes.csv",
            "rate_cards.csv",
            "shipments.csv",
            "shipment_legs.csv",
            "weight_measurements.csv",
            "accessorials.csv",
            "freight_invoices.csv",
            "invoice_lines.csv",
            "audit_exceptions.csv",
            "credit_notes.csv",
            "ground_truth.csv",
            "ground_truth.json"
        ]

        all_matched = True

        for fname in files_to_check:
            f1 = dir_run1 / fname
            f2 = dir_run2 / fname

            if not f1.exists() or not f2.exists():
                print(f"{fname:<30} | MISSING FILE ERROR")
                all_matched = False
                continue

            h1 = compute_file_sha256(f1)
            h2 = compute_file_sha256(f2)

            # Count rows for csv
            r1_rows = sum(1 for _ in open(f1, "r", encoding="utf-8")) if fname.endswith(".csv") else "N/A"
            r2_rows = sum(1 for _ in open(f2, "r", encoding="utf-8")) if fname.endswith(".csv") else "N/A"

            matched = (h1 == h2 and r1_rows == r2_rows)
            if not matched:
                all_matched = False

            status_str = "PASS" if matched else "FAIL"
            print(f"{fname:<30} | {str(r1_rows):<10} | {str(r2_rows):<10} | {h1[:20]}... | {status_str}")

        print("=" * 92)
        if all_matched:
            print("REPRODUCIBILITY RESULT: SUCCESS! 100% Deterministic match across all tables.")
            return True
        else:
            print("REPRODUCIBILITY RESULT: FAILED! Mismatch detected.")
            assert False, "Reproducibility checksum mismatch detected across runs"
            return False

    finally:
        # Cleanup temporary run directories
        if dir_run1.exists():
            shutil.rmtree(dir_run1)
        if dir_run2.exists():
            shutil.rmtree(dir_run2)

if __name__ == "__main__":
    success = test_reproducibility()
    if not success:
        sys.exit(1)
