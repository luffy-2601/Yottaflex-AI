"""
Evaluation and Metrics Engine for Freight Invoice Audit Solution.
Compares automated audit engine findings against ground_truth.csv.
Computes:
- Precision, Recall, F1-Score, Accuracy
- Confusion Matrix (TP, FP, TN, FN)
- Anomaly-type specific detection rates
- Financial Overcharge Recovery Metrics & Dollar Variance Reconciliation
"""
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_DIR
from src.audit_engine import FreightAuditEngine

class AuditEvaluator:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir

    def evaluate(self, audit_results: List[Dict[str, Any]], ground_truth_file: str = "ground_truth.csv") -> Dict[str, Any]:
        """Evaluate audit findings against isolated ground truth labels."""
        gt_path = self.data_dir / ground_truth_file
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_records = list(csv.DictReader(f))

        gt_by_invoice = {r["invoice_id"]: r for r in gt_records}

        tp = 0  # Expected Dispute, Audit flagged Dispute
        fp = 0  # Expected Clean, Audit flagged Dispute
        tn = 0  # Expected Clean, Audit flagged Clean
        fn = 0  # Expected Dispute, Audit flagged Clean

        anomaly_stats: Dict[str, Dict[str, int]] = {}
        total_gt_disputed_usd = 0.0
        total_detected_disputed_usd = 0.0

        for res in audit_results:
            inv_id = res["invoice_id"]
            gt = gt_by_invoice.get(inv_id)
            if not gt:
                continue

            gt_is_anomaly = (gt["is_anomaly"] in ("True", True, 1, "1"))
            gt_type = gt.get("anomaly_type", "NONE")
            audit_dispute = (res["audit_decision"] == "DISPUTE")

            if gt_is_anomaly:
                total_gt_disputed_usd += float(gt["expected_disputed_amount"])
                if gt_type not in anomaly_stats:
                    anomaly_stats[gt_type] = {"total": 0, "detected": 0}
                anomaly_stats[gt_type]["total"] += 1

            if audit_dispute:
                total_detected_disputed_usd += res["variance_usd"]

            if gt_is_anomaly and audit_dispute:
                tp += 1
                if gt_type in anomaly_stats:
                    anomaly_stats[gt_type]["detected"] += 1
            elif not gt_is_anomaly and audit_dispute:
                fp += 1
            elif not gt_is_anomaly and not audit_dispute:
                tn += 1
            elif gt_is_anomaly and not audit_dispute:
                fn += 1

        total_samples = tp + fp + tn + fn
        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1_score = round(2 * (precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0
        accuracy = round((tp + tn) / total_samples, 4) if total_samples > 0 else 0.0

        # Detailed breakdown per anomaly type
        anomaly_breakdown = {}
        for atype, counts in anomaly_stats.items():
            tot = counts["total"]
            det = counts["detected"]
            rate = round(det / tot, 4) if tot > 0 else 0.0
            anomaly_breakdown[atype] = {
                "ground_truth_count": tot,
                "successfully_detected": det,
                "detection_rate": rate
            }

        return {
            "evaluation_metrics": {
                "total_invoices_evaluated": total_samples,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score
            },
            "confusion_matrix": {
                "true_positives": tp,
                "false_positives": fp,
                "true_negatives": tn,
                "false_negatives": fn
            },
            "anomaly_detection_breakdown": anomaly_breakdown,
            "financial_reconciliation": {
                "ground_truth_disputed_usd": round(total_gt_disputed_usd, 2),
                "audit_identified_variance_usd": round(total_detected_disputed_usd, 2),
                "financial_dollar_recovery_accuracy": round(min(total_detected_disputed_usd, total_gt_disputed_usd) / max(total_detected_disputed_usd, total_gt_disputed_usd), 4) if max(total_detected_disputed_usd, total_gt_disputed_usd) > 0 else 1.0
            }
        }

if __name__ == "__main__":
    engine = FreightAuditEngine()
    audit_output = engine.audit_all()
    
    evaluator = AuditEvaluator()
    eval_results = evaluator.evaluate(audit_output["audit_results"])
    
    print("=== AUDIT EVALUATION REPORT ===")
    print(json.dumps(eval_results, indent=2))

