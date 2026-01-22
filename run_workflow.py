import json
from graph.workflow_manager import workflow
from utils.disk_cache import load

patients = json.loads(
    open("data/patients/synthetic_patients.json").read()
)

embed_cache = load("embedding_cache", "global") or {}

for patient in patients[:5]:
    state = {
        "patient": patient,
        "embed_cache": embed_cache,
        "max_trials": 10
    }

    result = workflow.invoke(state)
    print(f"✅ {patient['patient_id']} done")
