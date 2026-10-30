"""
Master End-to-End Pipeline Runner for Freight Invoice Audit Solution.
Executes complete workflow in sequence:
1. Synthetic Data Generation (11 entities + ground truth)
2. Automated Relational and Arithmetic Validation (Step 8)
3. Freight Invoice Audit & Re-rating Engine
4. Evaluation vs Ground Truth (Precision, Recall, F1, ROI)
5. Reproducibility Check (Step 10)
6. Markdown and Interactive HTML Report Generation
"""
import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_SEED, DATA_DIR, REPORTS_DIR
from src.generator import FreightDataGenerator
from src.validator import DataValidator
from src.audit_engine import FreightAuditEngine
from src.evaluation import AuditEvaluator
from src.report_generator import ReportGenerator
from scripts.test_reproducibility import run_reproducibility_test

def run_pipeline(scale: str = "starter", seed: int = DEFAULT_SEED, verify_reproducibility: bool = True):
    start_time = time.time()
    print("=" * 80)
    print("  FREIGHT INVOICE AUDIT & DISPUTE RECONCILIATION PIPELINE")
    print(f"  Scale Profile: {scale.upper()} | Fixed Seed: {seed}")
    print("=" * 80)

    # 1. Generate Synthetic Data
    print("\n[Step 1/5] Generating deterministic relational synthetic dataset...")
    gen = FreightDataGenerator(seed=seed, scale=scale)
    gen.generate_all()
    manifest = gen.export_all(DATA_DIR)
    print(f"  -> Generated {manifest['table_counts']['freight_invoices']:,} invoices across {manifest['table_counts']['carriers']:,} carriers.")

    # 2. Run Data Validation
    print("\n[Step 2/5] Running relational integrity & arithmetic validator (Step 8)...")
    validator = DataValidator(data_dir=DATA_DIR)
    val_results = validator.validate_all()
    v_summary = val_results["summary"]
    print(f"  -> {v_summary['checks_performed']:,} checks evaluated: {v_summary['checks_passed']:,} passed, {v_summary['violations_found']} violations.")
    if not v_summary["validation_passed"]:
        print("  [ERROR] Validation failed!")
        sys.exit(1)

    # 3. Run Freight Audit & Rating Engine
    print("\n[Step 3/5] Executing Freight Audit & Rating Engine...")
    engine = FreightAuditEngine(data_dir=DATA_DIR)
    audit_output = engine.audit_all()
    a_summary = audit_output["summary"]
    print(f"  -> Audited {a_summary['total_invoices_audited']:,} invoices: {a_summary['clean_invoices']:,} clean, {a_summary['disputed_invoices']:,} disputed.")
    print(f"  -> Identified ${a_summary['total_disputed_amount_usd']:,.2f} in overcharges across {a_summary['total_exceptions_raised']:,} exceptions.")

    # 4. Evaluate against Ground Truth
    print("\n[Step 4/5] Evaluating decisions against isolated ground truth...")
    evaluator = AuditEvaluator(data_dir=DATA_DIR)
    eval_results = evaluator.evaluate(audit_output["audit_results"])
    metrics = eval_results["evaluation_metrics"]
    print(f"  -> Accuracy: {metrics['accuracy']*100:.1f}% | Precision: {metrics['precision']*100:.1f}% | Recall: {metrics['recall']*100:.1f}% | F1: {metrics['f1_score']:.4f}")

    # 5. Reproducibility Test
    if verify_reproducibility:
        print("\n[Step 5/5] Running Step 10 Reproducibility Check (Dual run with SHA-256)...")
        repro_pass = run_reproducibility_test(seed=seed, scale="starter")
        if not repro_pass:
            print("  [ERROR] Reproducibility verification failed!")
            sys.exit(1)

    # 6. Generate Reports
    print("\n[Generating Reports] Producing Markdown & Interactive HTML Dashboards...")
    reporter = ReportGenerator(output_dir=REPORTS_DIR)
    reporter.generate_reports(manifest, val_results, audit_output, eval_results)

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"  PIPELINE EXECUTION COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    print(f"  Reports: {REPORTS_DIR / 'AUDIT_REPORT.md'}")
    print(f"           {REPORTS_DIR / 'audit_dashboard.html'}")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Freight Audit Pipeline Runner")
    parser.add_argument("--scale", choices=["starter", "medium", "full"], default="starter", help="Dataset volume scale")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Fixed deterministic seed")
    parser.add_argument("--no-repro", action="store_true", help="Skip dual-run reproducibility test")
    args = parser.parse_args()

    run_pipeline(scale=args.scale, seed=args.seed, verify_reproducibility=not args.no_repro)

