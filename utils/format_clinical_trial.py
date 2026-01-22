#Import and setup
import sys
import json
import os
import html
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
from openai import OpenAI

# Project root
PROJECT_ROOT = Path(r"C:\Projects\clinical_trial_agent")
sys.path.append(str(PROJECT_ROOT))

from utils.schema_validation import validate_data

# Environment & GPT Client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Project Paths
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "trials_filtered.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "trials_agent_ready.json"
CACHE_FILE = PROJECT_ROOT / "data" / "processed" / "trials_gpt_cache.json"
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Schema defination
CRITERIA_SCHEMA = {
    "type": "object",
    "properties": {
        "inclusion": {"type": "array","items": {"type": "string"}},
        "exclusion": {"type": "array","items": {"type": "string"}}
    },
    "required": ["inclusion", "exclusion"]
}

# GPT Extraction Logic
def extract_criteria(protocol_text: str) -> Dict:
    if not protocol_text or len(protocol_text.strip()) < 20:
        return {"inclusion": [], "exclusion": []}
    
#Text cleaning: convert html entities to normal characters

    clean_text = html.unescape(protocol_text)

    system_prompt = (
        "You are a clinical trial protocol analyst.\n"
        "Extract inclusion and exclusion criteria with medical precision.\n"
        "Return JSON only."
    )

    user_prompt = f"""
Extract inclusion and exclusion criteria from the protocol text below.

Rules:
- Output MUST be valid JSON
- No commentary, no markdown
- Each criterion must be a concise sentence
- Preserve numeric thresholds exactly
- If a section is missing, return an empty list

JSON schema:
{json.dumps(CRITERIA_SCHEMA, indent=2)}

Protocol Text:
\"\"\"
{clean_text}
\"\"\"
"""

#GPT API call
    response = client.responses.create(
        model="gpt-4o-mini",
        temperature=0,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
#Parse & Validate GPT output
    try:
        parsed = json.loads(response.output_text)
        validate_data(CRITERIA_SCHEMA, parsed)
        return parsed
    except Exception as e:
        print(f"⚠️ Extraction failed: {e}")
        return {"inclusion": [], "exclusion": []}

# GPT Cache Handling
def load_gpt_cache() -> Dict:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}    

def save_gpt_cache(cache: Dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

# Main Execution
if __name__ == "__main__":
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    # Load raw trials and GPT cache
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        trials = json.load(f)

    gpt_cache = load_gpt_cache()
    print(f"🚀 Formatting {len(trials)} clinical trials with GPT extraction...")

#Processed each trial
    processed = []
    new_extractions = 0
    for trial in trials:
        nct_id = trial["nct_id"]
        criteria_text = trial.get("eligibilityCriteria", "")

        #Check cache first
        if nct_id in gpt_cache:
            trial["Criteria"] = gpt_cache[nct_id]
        else:    
            criteria = extract_criteria(criteria_text)
            trial["Criteria"] = criteria
            gpt_cache[nct_id] = criteria
            new_extractions +=1

        # Remove large unused fields for RAG efficiency
        trial.pop("protocolSection", None)
        processed.append(trial)

    # Save agent_ready trials
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)
    
    # Save GPT cache for next runs
    save_gpt_cache(gpt_cache)

    print(f"✅ SUCCESS: Agent-ready trials saved to:{OUTPUT_FILE}")
    print(f"📂GPT calls made this run: {new_extractions}")
    print(f"Total cached trials: {len(gpt_cache)}")