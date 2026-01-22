#Import libraries)
import requests
import json
import os
from dotenv import load_dotenv

#Configuration
load_dotenv()  #read .env so store config values 

BASE_DIR = r"C:\Projects\clinical_trial_agent"
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "raw", "trials_filtered.json")
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

#Loading Existing Trials (Caching)
def load_existing_trials():
    """THE CATCH: Load existing data to avoid redundant processing."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

#Main Ingestion Function
def ingest_raw_trials(maximum_trials=100):
    print("🚀 STARTING API INGESTION...", flush=True)
    
    # Load existing "Catch" to prevent duplicates
    existing_data = load_existing_trials()
    existing_ids = {t["nct_id"] for t in existing_data if "nct_id" in t}
    print(f"📦 Found {len(existing_ids)} trials already in local storage.")
    
    #API Call Setup
    url = "https://clinicaltrials.gov/api/v2/studies"
    page_token = None   # used for pagination, 
    total_added = 0

    #Pagination Loop
    while total_added < maximum_trials:
        params = {
            "query.cond": "Diabetes",
            "filter.overallStatus": "RECRUITING",
            "pageSize": 50, # Maximize per-call efficiency
            "format": "json"
        }
        if page_token:
            params ["pageToken"] = page_token
        
        #Make API Call
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()        
        data = response.json()
        
        #Extract studies & pagination token
        studies = data.get("studies", [])
        page_token = data.get("nextPageToken")
        if not studies:
            break

        #Process each trial
        for study in studies:
            if total_added >= maximum_trials:
                break
            
        #Extracts
            protocol = study.get("protocolSection", {})
            ident = protocol.get("identificationModule", {})
            nct_id = ident.get("nctId")
        
        # CATCH LOGIC: Skip if we already have this NCT ID
            if not nct_id or nct_id in existing_ids:
                continue    

        #Extarct trial metadata        
            eligibility = protocol.get("eligibilityModule", {})
            trial_info = {
                "nct_id": nct_id,
                "title": ident.get("briefTitle"),
                "eligibilityCriteria": eligibility.get("eligibilityCriteria", "No criteria listed"),
                "minimumAge": eligibility.get("minimumAge"),
                "maximumAge": eligibility.get("maximumAge"),
                "sex": eligibility.get("sex"),
                "healthyVolunteers": eligibility.get("healthyVolunteers")
            }
            existing_data.append(trial_info)
            existing_ids.add(nct_id)
            total_added += 1

        #Stop condition for pagination
        if not page_token:
            break    

        #Write JSON File
    if total_added > 0:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2)
       
        #Final log
    print(f"✅ Added {total_added} new trials (total_stored: {len(existing_data)})")
    
    #Run script
if __name__ == "__main__":
    ingest_raw_trials()