import os
from pathlib import Path
from dotenv import load_dotenv

# -----------------------------
# Load .env variables
# -----------------------------
load_dotenv()

# -----------------------------
# Environment
# -----------------------------
DEVELOPMENT_MODE = True

# Base project directory
BASE_DIR = Path(__file__).resolve().parents[1]

# -----------------------------
# API Keys
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east1-gcp")

# -----------------------------
# Data Paths
# -----------------------------
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

TRIALS_RAW_FILE = RAW_DIR / "trials_filtered.json"
TRIALS_WITH_CRITERIA_FILE = PROCESSED_DIR / "trials_with_criteria.json"

# Ensure directories exist
for d in [RAW_DIR, PROCESSED_DIR]:
    os.makedirs(d, exist_ok=True)

