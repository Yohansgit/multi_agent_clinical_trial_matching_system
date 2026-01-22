# utils/med_vocab.py
NORM_MAP = {
    "t1d": "type 1 diabetes",
    "t2d": "type 2 diabetes",
    "htn": "hypertension",
    "high blood pressure": "hypertension"
}

def normalize(condition: str) -> str:
    return NORM_MAP.get(condition.lower(), condition.lower())
