import os
import json
from typing import List, Dict
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX", "clinical-trials")
OUTPUT_PATH = Path("data/matches/patient_trial_matches.json")
# 💰 CREDIT SAVER: Cache for embeddings
EMBED_CACHE_PATH = Path("data/cache/patient_embed_cache.json")

# Clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

def load_cache(path: Path) -> Dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(path: Path, data: Dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_embedding_with_cache(text: str, patient_id: str, cache: Dict) -> List[float]:
    """Checks cache first to save OpenAI credits."""
    if patient_id in cache:
        return cache[patient_id]
    
    print(f"💸 API CALL: Embedding patient {patient_id}...")
    resp = client.embeddings.create(model="text-embedding-3-small", input=text)
    embedding = resp.data[0].embedding
    
    # Update cache
    cache[patient_id] = embedding
    return embedding

def hybrid_search_and_reason(patient: Dict, embed_cache: Dict, top_k: int = 5) -> List[Dict]:
    # 1. Create a query 
    query_text = f"Trial for {', '.join(patient.get('conditions', []))}"
    
    # 2. Get embedding (Uses Catch/Cache)
    query_vec = get_embedding_with_cache(query_text, patient["patient_id"], embed_cache)

    # 3. Query Pinecone
    res = index.query(vector=query_vec, top_k=top_k, include_metadata=True)

    enriched_results = []
    patient_conds = [c.lower() for c in patient.get("conditions", [])]

    for match in res.get("matches", []):
        meta = match.get("metadata", {})
        
        # Parse Criteria safely
        criteria_raw = meta.get("structured_criteria")
        criteria_dict = json.loads(criteria_raw) if isinstance(criteria_raw, str) else {"inclusion": [], "exclusion": []}

        # Initial reasoning
        eligible = True
        reasons = []
        for rule in criteria_dict.get("exclusion", []):
            if any(cond in rule.lower() for cond in patient_conds):
                eligible = False
                reasons.append(f"Reasoning Engine Veto: {rule}")

        # Handoff context for the Critic
        enriched_results.append({
            "patient_id": patient["patient_id"],
            "nct_id": meta.get("nct_id"),
            "title": meta.get("title", ""),
            "eligible": eligible,
            "reasons": reasons,
            "match_score": round(match.get("score", 0), 4),
            "patient_summary": {
                "conditions": patient.get("conditions", []),
                "medications": patient.get("medications", [])
            },
            "Criteria": criteria_dict
        })

    return enriched_results

if __name__ == "__main__":
    # Load Catch
    embed_cache = load_cache(EMBED_CACHE_PATH)
    
    test_patient = {
        "patient_id": "PAT_0001",
        "conditions": ["Type 1 Diabetes", "Neuropathy"],
        "medications": ["Insulin"]
    }
    
    print(f"🧠 Reasoning Agent: Processing {test_patient['patient_id']}...")
    matches = hybrid_search_and_reason(test_patient, embed_cache)
    
    # Save Outputs
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2)
    
    # 💰 SAVE THE CATCH
    save_cache(EMBED_CACHE_PATH, embed_cache)
    
    print(f"✅ Handoff file created for Critic: {OUTPUT_PATH}")
