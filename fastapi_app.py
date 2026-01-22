from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="🧬 Clinical Trial Eligibility API",
    description="Check patient eligibility for trials with JSON or HTML (clinician-friendly) output.",
    version="1.1"
)

# -----------------------------
# Patient Model (optional fields, examples for Swagger)
# -----------------------------
class PatientCriteria(BaseModel):
    age: Optional[int] = Field(None, description="Patient age in years", example=55)
    sex: Optional[str] = Field(None, description="Patient sex (male/female/other)", example="female")
    conditions: Optional[List[str]] = Field([], description="List of medical conditions", example=["diabetes"])
    medications: Optional[List[str]] = Field([], description="List of current medications", example=["metformin"])

# -----------------------------
# Sample Trials
# -----------------------------
TRIALS = [
    {"trial_id": 1, "name": "Trial A", "min_age": 18, "max_age": 65, "exclude_conditions": ["cancer"]},
    {"trial_id": 2, "name": "Trial B", "min_age": 50, "max_age": 80, "exclude_conditions": []},
    {"trial_id": 3, "name": "Trial C", "min_age": 30, "max_age": 60, "exclude_conditions": ["diabetes"]}
]

# -----------------------------
# Eligibility Logic
# -----------------------------
def evaluate_trial(patient, trial):
    reasons = []

    # Age check
    if patient.get("age") is not None:
        if not (trial["min_age"] <= patient["age"] <= trial["max_age"]):
            reasons.append(f"Age {patient['age']} not in range {trial['min_age']}-{trial['max_age']}")
    else:
        reasons.append("Age not provided")

    # Conditions check
    patient_conditions = patient.get("conditions") or []
    excluded_conditions = [c for c in patient_conditions if c in trial["exclude_conditions"]]
    if excluded_conditions:
        reasons.append(f"Excluded conditions: {', '.join(excluded_conditions)}")

    eligible = len(reasons) == 0
    reason_text = "Eligible" if eligible else "; ".join(reasons)

    return {
        "trial_id": trial["trial_id"],
        "name": trial["name"],
        "eligible": eligible,
        "reason": reason_text
    }

# -----------------------------
# JSON Response Endpoint
# -----------------------------
@app.post("/check_eligibility")
def check_eligibility(patient: PatientCriteria):
    patient_data = patient.dict()
    trials_result = [evaluate_trial(patient_data, t) for t in TRIALS]

    eligible_trials = [t for t in trials_result if t["eligible"]]
    ineligible_trials = [t for t in trials_result if not t["eligible"]]

    return {
        "patient": patient_data,
        "eligible_trials": eligible_trials,
        "ineligible_trials": ineligible_trials
    }

# -----------------------------
# HTML Response Endpoint (clinician-friendly)
# -----------------------------
@app.post("/check_eligibility_html", response_class=HTMLResponse)
def check_eligibility_html(patient: PatientCriteria):
    patient_data = patient.dict()
    trials_result = [evaluate_trial(patient_data, t) for t in TRIALS]

    eligible_trials = [t for t in trials_result if t["eligible"]]
    ineligible_trials = [t for t in trials_result if not t["eligible"]]

    html = f"""
    <html>
    <head>
        <title>Clinical Trial Eligibility</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.5; }}
            .trial {{ margin-bottom: 5px; }}
            .eligible {{ color: green; font-weight: bold; }}
            .ineligible {{ color: red; font-weight: bold; }}
            .section-title {{ margin-top: 15px; font-size: 1.1em; text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h2>Patient Info</h2>
        <p>Age: {patient_data.get('age', 'N/A')}</p>
        <p>Sex: {patient_data.get('sex', 'N/A')}</p>
        <p>Conditions: {', '.join(patient_data.get('conditions', []) or ['None'])}</p>
        <p>Medications: {', '.join(patient_data.get('medications', []) or ['None'])}</p>

        <div class="section-title">Eligible Trials</div>
        {"<br>".join([f'<div class="trial eligible">{t["trial_id"]}. {t["name"]} ✅ {t["reason"]}</div>' for t in eligible_trials]) or "<p>None</p>"}

        <div class="section-title">Ineligible Trials</div>
        {"<br>".join([f'<div class="trial ineligible">{t["trial_id"]}. {t["name"]} ❌ {t["reason"]}</div>' for t in ineligible_trials]) or "<p>None</p>"}
    </body>
    </html>
    """

    return html
