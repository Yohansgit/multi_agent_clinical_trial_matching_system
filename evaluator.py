# utils/evaluator_cached.py

import json
from pathlib import Path
from utils.disk_cache import load, save  # your existing disk_cache

# ==============================
# Configuration
# ==============================
BASE_DIR = Path(r"C:\Projects\clinical_trial_agent")
GT_FILE = BASE_DIR / "data/ground_truth/ground_truth.json"
PRED_FILE = BASE_DIR / "data/matches/final_workflow_report.json"

CACHE_NAME = "evaluation_metrics"
CACHE_KEY = "latest_run"

# ==============================
# Helpers
# ==============================
def load_json(path):
    if not path.exists():
        print(f"❌ Error: File not found at {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def flatten_data(data, trial_key):
    flat_map = {}
    for entry in data:
        p_id = str(entry.get("patient_id", "")).strip().upper()
        trials = entry.get(trial_key, [])
        for trial in trials:
            t_id = str(trial.get("nct_id", "")).strip().upper()
            if p_id and t_id:
                flat_map[f"{p_id}|{t_id}"] = trial.get("eligible", False)
    return flat_map

# ==============================
# Evaluation
# ==============================
def evaluate_performance():
    # 1️ Try loading cached metrics
    cached = load(CACHE_NAME, CACHE_KEY)
    if cached:
        print("⚡ Using cached evaluation metrics:")
        print(json.dumps(cached, indent=4))
        return

    # 2️ Load data
    gt_data = load_json(GT_FILE)
    pred_data = load_json(PRED_FILE)
    if not gt_data or not pred_data:
        return

    # 3️ Flatten
    gt_flat = flatten_data(gt_data, "matches")
    pred_flat = flatten_data(pred_data, "verified_trials")

    # 4️ Compute TP, FP, TN, FN
    tp = fp = tn = fn = 0
    for key, is_eligible_gt in gt_flat.items():
        is_eligible_pred = pred_flat.get(key, False)
        if is_eligible_gt and is_eligible_pred:
            tp += 1
        elif not is_eligible_gt and is_eligible_pred:
            fp += 1
        elif not is_eligible_gt and not is_eligible_pred:
            tn += 1
        elif is_eligible_gt and not is_eligible_pred:
            fn += 1

    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    accuracy = (tp + tn) / total if total else 0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0

    results = {
        "Metrics": {
            "Accuracy": f"{accuracy:.2%}",
            "Precision": f"{precision:.2%}",
            "Recall": f"{recall:.2%}",
            "F1_Score": round(f1, 4)
        },
        "Counts": {
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
            "Total": total
        }
    }

    # 5️ Save cache
    save(CACHE_NAME, CACHE_KEY, results)

    print("\n=== 📊 Clinical Agent Evaluation Report ===")
    print(json.dumps(results, indent=4))
    print("\n✅ Metrics cached for future runs.")

# ==============================
# Main
# ==============================
if __name__ == "__main__":
    evaluate_performance()
