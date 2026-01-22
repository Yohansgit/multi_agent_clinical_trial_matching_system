import json
from pathlib import Path

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _path(namespace: str) -> Path:
    return CACHE_DIR / f"{namespace}.json"

def load(namespace: str, key: str):
    path = _path(namespace)
    if not path.exists():
        return None

    data = json.loads(path.read_text())
    return data.get(key)

def save(namespace: str, key: str, value):
    path = _path(namespace)

    data = {}
    if path.exists():
        data = json.loads(path.read_text())

    data[key] = value
    path.write_text(json.dumps(data, indent=2))
