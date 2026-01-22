# utils/sync_ground_truth.py

import json
from pathlib import Path
from typing import Dict, Any, List
from utils.disk_cache import load, save  # simple persistent cache

# ==============================
# 1️⃣ Configuration & Paths
# ==============================
BASE_DIR = Path(r"C:\Projects\clinical_trial_agent")
GROUND_TRUTH_DIR = BASE_DIR / "data/ground_truth"
GROUND_TRUTH_FILE = GROUND_TRUTH_DIR / "ground_truth.json"

# Candidate workflow outputs (auto-detect)
WORKFLOW_CANDIDATES = [
    BASE_DIR / "data/matches/final_workflow_report.json",
    BASE_DIR / "data/matches/patient_trial_matches.json",
]

# ==============================
# 2️⃣ Deterministic Ground Truth Logic
# ==============================
def determine_truth(patient: Dict[str, Any], trial: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns deterministic eligibility and reason.
    Uses caching to save computation.
    """
    key = {"patient_id": patient["patient_id"], "trial_id": trial["nct_id"]}

    # ✅ Check cache first
    cached = load("ground_truth", key)
    if cached:
        return cached

    patient_conditions = [c.lower() for c in patient.get("conditions", [])]
    trial_title = trial.get("title", "").lower()

    eligible = False
    reason = "No matching condition found in trial title."

    for cond in patient_conditions:
        if cond in trial_title:
            eligible = True
            reason = f"Deterministic match: Patient condition '{cond}' found in trial title."
            break

    result = {"eligible": eligible, "reason": reason}

    # 💾 Save to cache immediately
    save("ground_truth", key, result)
    return result

# ==============================
# 3️⃣ Main Sync Function
# ==============================
def sync_ground_truth():
    print("🔄 Starting Ground Truth sync...")

    # Auto-detect workflow output
    workflow_file = None
    for candidate in WORKFLOW_CANDIDATES:
        if candidate.exists():
            workflow_file = candidate
            break

    if workflow_file is None:
        print("❌ Error: Run your workflow first to generate matches!")
        return

    # Load workflow matches
    with open(workflow_file, "r", encoding="utf-8") as f:
        workflow_data = json.load(f)

    # Load patient source for conditions
    PATIENTS_PATH = BASE_DIR / "data/patients/synthetic_patients.json"
    if not PATIENTS_PATH.exists():
        print(f"❌ Error: Patient source file not found at {PATIENTS_PATH}")
        return

    with open(PATIENTS_PATH, "r", encoding="utf-8") as f:
        patients = {p["patient_id"]: p for p in json.load(f)}

    # Prepare ground truth list
    ground_truth_output: List[Dict[str, Any]] = []

    for entry in workflow_data:
        p_id = entry.get("patient_id")
        patient = patients.get(p_id)
        if not patient:
            continue

        matches = []
        for trial_entry in entry.get("verified_trials", []):
            nct_id = trial_entry.get("nct_id")
            trial = trial_entry
            truth = determine_truth(patient, trial)
            matches.append({
                "nct_id": nct_id,
                "eligible": truth["eligible"],
                "reasons": [truth["reason"]]
            })

        ground_truth_output.append({
            "patient_id": p_id,
            "matches": matches
        })

    # Ensure directory exists
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    # Save final ground truth
    with open(GROUND_TRUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(ground_truth_output, f, indent=2)

    print(f"✅ Ground Truth synced for {len(ground_truth_output)} patients.")
    print(f"📂 Saved at: {GROUND_TRUTH_FILE}")

# ==============================
# 4️⃣ CLI Entry Point
# ==============================
if __name__ == "__main__":
    sync_ground_truth()
