from typing import Dict, List
import json
import hashlib
from utils.disk_cache import load, save

# ----------------------------------
# Utilities
# ----------------------------------
def normalize(items: List[str]) -> List[str]:
    return [i.lower().strip() for i in items if i]


def _cache_key(criteria: Dict, patient_summary: Dict) -> str:
    """Stable hash for criteria + patient"""
    payload = {
        "criteria": criteria,
        "patient": patient_summary
    }
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()

# ----------------------------------
# 1️⃣ FAST RULE-BASED CRITIC
# ----------------------------------
def rule_critic_verify(criteria: Dict, patient_summary: Dict) -> Dict:
    """
    STRICT RULES:
    - Any exclusion match → INELIGIBLE
    - At least one inclusion match required
    """

    key = _cache_key(criteria, patient_summary)

    # 💰 HARD CACHE HIT
    cached = load("critic_agent", key)
    if cached:
        return cached

    inclusion = normalize(criteria.get("inclusion", []))
    exclusion = normalize(criteria.get("exclusion", []))
    patient_conds = normalize(patient_summary.get("conditions", []))

    # 🚫 HARD EXCLUSION
    for exc in exclusion:
        if any(pc in exc for pc in patient_conds):
            result = {
                "eligible": False,
                "reasons": [f"Hard exclusion matched: {exc}"],
                "confidence": "high"
            }
            save("critic_agent", key, result)
            return result

    # ✅ INCLUSION REQUIRED
    inc_match = any(
        any(pc in inc for pc in patient_conds)
        for inc in inclusion
    )

    if not inc_match:
        result = {
            "eligible": False,
            "reasons": ["No inclusion criteria satisfied"],
            "confidence": "high"
        }
        save("critic_agent", key, result)
        return result

    result = {
        "eligible": True,
        "reasons": ["Inclusion met, no exclusions"],
        "confidence": "high"
    }

    save("critic_agent", key, result)
    return result

# ----------------------------------
# 2️⃣ OPTIONAL LLM CRITIC (FUTURE)
# ----------------------------------
def llm_critic_verify(criteria: Dict, patient_summary: Dict, strict: bool = False) -> Dict:
    """
    Placeholder for GPT-based verification
    (Not implemented yet)
    """
    return {
        "eligible": True,
        "reasons": ["LLM deep verification placeholder"],
        "confidence": "low"
    }

# ----------------------------------
# 3️⃣ ORCHESTRATOR (WHAT YOU CALL)
# ----------------------------------
def critic_verify(criteria: Dict, patient_summary: Dict) -> Dict:
    """
    Default critic = fast deterministic logic
    Upgrade to LLM only if needed
    """
    return rule_critic_verify(criteria, patient_summary)
