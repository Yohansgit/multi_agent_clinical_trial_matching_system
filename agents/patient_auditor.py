import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

# Add the project root to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.app_logger import get_logger

# 1. Configuration & Clients
load_dotenv()
logger = get_logger("PatientAuditor")

# Environment Variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX", "clinical-trials")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Paths
PATIENTS_PATH = Path(r"C:\Projects\clinical_trial_agent\data\patients\synthetic_patients.json")
OUTPUT_PATH = Path(r"C:\Projects\clinical_trial_agent\data\matches\patient_trial_matches.json")

# Matching Parameters
MAX_PATIENTS = 10
TOP_K_TRIALS = 5  # Number of trials to retrieve from Pinecone per patient

# Initialize Clients
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# 2. Pydantic Models
class Criteria(BaseModel):
    inclusion: List[str] = []
    exclusion: List[str] = []

class Trial(BaseModel):
    nct_id: str
    title: str
    criteria: Criteria

# 3. Agent Functions
def get_embedding(text: str) -> List[float]:
    """Generate 1536-dim embedding using OpenAI text-embedding-3-small."""
    resp = client.embeddings.create(model="text-embedding-3-small", input=text)
    return resp.data[0].embedding

def llm_audit_eligibility(patient: Dict, trial: Trial) -> Dict:
    """Agentic reasoning using gpt-4o-mini to verify eligibility."""
    prompt = f"""
    You are a Clinical Trial Auditor. Determine if the patient is eligible for the trial.
    
    PATIENT PROFILE:
    - Age: {patient['demographics']['age']}
    - Sex: {patient['demographics']['sex']}
    - Conditions: {patient.get('conditions', [])}
    - Medications: {patient.get('medications', [])}
    
    CLINICAL TRIAL ({trial.nct_id}):
    - Title: {trial.title}
    - Inclusion Criteria: {trial.criteria.inclusion}
    - Exclusion Criteria: {trial.criteria.exclusion}
    
    Return a JSON object:
    {{
      "eligible": boolean,
      "reasoning": "Explain why in one short sentence, citing specific criteria."
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise medical auditor. Return JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"❌ LLM Audit failed for {trial.nct_id}: {e}")
        return {"eligible": False, "reasoning": "Internal auditor error."}

# 4. Main Execution Pipeline
def run_auditor():
    if not PATIENTS_PATH.exists():
        logger.error(f"❌ Patient file not found: {PATIENTS_PATH}")
        return

    # Load Patients
    with open(PATIENTS_PATH, "r", encoding="utf-8") as f:
        patients = json.load(f)

    all_matches = []

    for p_raw in patients[:MAX_PATIENTS]:
        p_id = p_raw.get("patient_id")
        conditions = p_raw.get("conditions", [])
        
        logger.info(f"🚀 Auditing Patient {p_id} ({', '.join(conditions)})")

        # STEP 1: Vector Search (Retrieval)
        # We query Pinecone using the patient's conditions
        search_query = f"Clinical trial treating {', '.join(conditions)}"
        query_vec = get_embedding(search_query)
        
        search_results = index.query(
            vector=query_vec, 
            top_k=TOP_K_TRIALS, 
            include_metadata=True
        )

        # STEP 2: Agentic Audit
        for match in search_results["matches"]:
            meta = match["metadata"]
            
            # Reconstruct Trial from Pinecone Metadata
            try:
                # We stored Criteria as a JSON string in Pinecone to avoid 'null' issues
                criteria_data = json.loads(meta.get("structured_criteria", "{}"))
                trial = Trial(
                    nct_id=meta["nct_id"],
                    title=meta["title"],
                    criteria=Criteria(**criteria_data)
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse metadata for {meta.get('nct_id')}: {e}")
                continue

            # Reason with gpt-4o-mini
            audit = llm_audit_eligibility(p_raw, trial)

            match_entry = {
                "patient_id": p_id,
                "nct_id": trial.nct_id,
                "vector_score": round(match["score"], 4),
                "eligible": audit["eligible"],
                "reasoning": audit["reasoning"]
            }
            all_matches.append(match_entry)
            
            status = "✅" if audit["eligible"] else "❌"
            logger.info(f"  {status} Trial {trial.nct_id}: {audit['reasoning']}")

    # STEP 3: Save results
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, indent=2)
    
    logger.info(f"🏁 Matching complete. {len(all_matches)} audits saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    run_auditor()
