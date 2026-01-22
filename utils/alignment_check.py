import json
import sys
import os
from pathlib import Path

# Add project root to path for imports
BASE_DIR = Path(r"C:\Projects\clinical_trial_agent")
sys.path.append(str(BASE_DIR))

# Paths to your "Agent Results" and your "Independent Judge Results"
PRED_FILE = BASE_DIR / "data/matches/final_workflow_report.json"
GT_FILE = BASE_DIR / "data/ground_truth/ground_truth.json"

def check_alignment():
    if not PRED_FILE.exists() or not GT_FILE.exists():
        print("❌ Error: Missing files. Ensure both Workflow and Honest Sync have run.")
        return

    # Load and Flatten Agent Predictions
    preds = {}
    for p in json.load(open(PRED_FILE, encoding="utf-8")):
        for t in p.get('verified_trials', []):
            preds[f"{p['patient_id']}|{t['nct_id']}"] = t

    # Load and Flatten Judge Ground Truth
    gts = {}
    for p in json.load(open(GT_FILE, encoding="utf-8")):
        for m in p.get('matches', []):
            gts[f"{p['patient_id']}|{m['nct_id']}"] = m

    print(f"\n--- 🔍 CONFLICT ANALYSIS (Comparing Agent vs Judge) ---")
    
    mismatch_count = 0
    for key in gts:
        if key not in preds: continue
        
        p_val = preds[key]
        gt_val = gts[key]
        
        # Only show where they DISAGREE
        if p_val['eligible'] != gt_val['eligible']:
            mismatch_count += 1
            print(f"\n📍 KEY: {key}")
            print(f"   🤖 AGENT: {'✅ Eligible' if p_val['eligible'] else '❌ Ineligible'}")
            print(f"   💬 Agent Reason: {p_val['reasoning']}")
            print(f"   ⚖️ JUDGE: {'✅ Eligible' if gt_val['eligible'] else '❌ Ineligible'}")
            print(f"   💬 Judge Reason: {gt_val['reasons']}")
        
        if mismatch_count >= 5: # Just show the first 5 to diagnose
            break
            
    if mismatch_count == 0:
        print("✅ No logical conflicts found in the sample.")

if __name__ == "__main__":
    check_alignment()
