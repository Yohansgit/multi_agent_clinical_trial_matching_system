#Import libraries
import sys
import json
import random
import os
from pathlib import Path

# Project Setup
PROJECT_ROOT = Path(r"C:\Projects\clinical_trial_agent")
sys.path.append(str(PROJECT_ROOT))

from utils.schema_validation import validate_data

# Paths
OUTPUT_PATH = PROJECT_ROOT / "data" / "patients" / "synthetic_patients.json"
SCHEMA_PATH = PROJECT_ROOT / "data" / "schemas" / "patient_schema.json"

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Load Patient Schema
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    patient_schema = json.load(f)

# Synthetic Data Generation Config
NUM_PATIENTS = 6000

conditions_pool = [
    "Type 2 Diabetes",
    "Type 1 Diabetes",
    "Hypertension",
    "Obesity",
    "Asthma",
]

medications_pool = [
    "Metformin",
    "Insulin",
    "Lisinopril",
    "Atorvastatin",
]

patients = []

print(f"🚀 Generating {NUM_PATIENTS} synthetic patients...")

# Generate Patients (loop)
for i in range(NUM_PATIENTS):
    patient = {
        "patient_id": f"PAT_{i+1:05d}",
        "demographics": {
            "age": random.randint(18, 85),
            "sex": random.choice(["Male", "Female"]),
            "bmi": round(random.uniform(18.5, 45.0), 1),
        },
        "conditions": random.sample(conditions_pool, random.randint(1, 2)),
        "medications": random.sample(medications_pool, random.randint(0, 2)),
        "RAGText": "Synthetic EHR record for agentic clinical trial matching."
    }

    try:
        validate_data(patient_schema, patient)
        patients.append(patient)
    except Exception as e:
        print(f"❌ Validation error on patient {patient['patient_id']}: {e}")

# Save Output
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(patients, f, indent=2)

print(f"✅ SUCCESS: Saved {len(patients)} patients to:")
print(f"📂 {OUTPUT_PATH}")
