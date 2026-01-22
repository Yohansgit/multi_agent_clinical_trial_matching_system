import os
import json
import hashlib
from pathlib import Path
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv
from utils.app_logger import get_logger

# 1. Config & Logger
load_dotenv()
logger = get_logger("ProtocolAgent")

# THE CACH: Save parsed JSON to avoid re-parsing same text
PROTOCOL_CACHE_PATH = Path(r"C:\Projects\clinical_trial_agent\data\cache\protocol_parsing_cache.json")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. Logic: The Specialist
class ProtocolAgent:
    def __init__(self):
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        if PROTOCOL_CACHE_PATH.exists():
            with open(PROTOCOL_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        PROTOCOL_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PROTOCOL_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def parse_criteria(self, raw_text: str) -> Dict:
        """
        Converts unstructured trial text into a clean Inclusion/Exclusion Dict.
        Uses Caching to save credits.
        """
        if not raw_text or len(raw_text.strip()) < 10:
            return {"inclusion": [], "exclusion": []}

        # 1. Check the Catch (Hash of the text)
        text_hash = hashlib.md5(raw_text.encode()).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]

        # 2. API Call (If not in catch)
        logger.info("💸 API CALL: GPT parsing new protocol text...")
        prompt = f"""
        Extract clinical trial eligibility criteria from the text below. 
        Format as JSON with 'inclusion' and 'exclusion' lists of strings.
        
        TEXT:
        {raw_text}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a clinical data scientist. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            structured_data = json.loads(response.choices[0].message.content)
            
            # 3. Update the Catch
            self.cache[text_hash] = structured_data
            self._save_cache()
            
            return structured_data
        except Exception as e:
            logger.error(f"❌ Protocol parsing failed: {e}")
            return {"inclusion": [], "exclusion": []}

# 3. Main Execution (Test)
if __name__ == "__main__":
    agent = ProtocolAgent()
    
    sample_text = "Patients must be 18+ and have Asthma. Exclude if pregnant."
    result = agent.parse_criteria(sample_text)
    
    print(f"Parsed Protocol: {json.dumps(result, indent=2)}")
