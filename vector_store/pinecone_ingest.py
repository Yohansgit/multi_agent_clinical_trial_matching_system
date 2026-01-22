#Import libraries
import os
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv
import pinecone
from openai import OpenAI

# 1. Environment & Config
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX", "clinical-trials")
TRIALS_PATH = Path(r"C:\Projects\clinical_trial_agent\data\processed\trials_agent_ready.json")

# THE CATCH: Persistent Trial Embedding Cache
CACHE_PATH = Path(r"C:\Projects\clinical_trial_agent\data\cache\trial_vector_cache.json")

pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# 2. Ensure Index Exists
if INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
    print(f"⚡ Creating Pinecone index '{INDEX_NAME}'...")
    from pinecone import ServerlessSpec
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )

index = pc.Index(INDEX_NAME)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 3. Embedding Function
def get_embedding(text: str, nct_id: str, cache: dict):
    """Checks the 'catch' before calling OpenAI API."""

    # Generate a hash of the text to detect if trial content changed
    content_hash = hashlib.md5(text.encode()).hexdigest()
    
    if nct_id in cache and cache[nct_id].get("hash") == content_hash:
        return cache[nct_id]["values"]

    print(f"💸 API CALL: Embedding Trial {nct_id}...")
    try:
        res = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        vector = res.data[0].embedding

        # Update catch
        cache[nct_id] = {"values": vector, "hash": content_hash}
        return vector
    except Exception as e:
        print(f"❌ Embedding failed for {nct_id}: {e}")
        return None

# 4. Ingest Logic
def ingest_structured_trials():
    if not TRIALS_PATH.exists():
        print(f"❌ Error: {TRIALS_PATH} not found.")
        return

    # Load Catch
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cached_vectors = {}
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cached_vectors = json.load(f)

    with open(TRIALS_PATH, "r", encoding="utf-8") as f:
        trials = json.load(f)

    print(f"🚀 Upserting {len(trials)} trials (Checking catch first)...")
    vectors_to_upsert = []

    for trial in trials:
        nct_id = str(trial.get("nct_id") or trial.get("NCTId"))
        if not nct_id: continue

        # Standardized text for embedding
        text_to_embed = f"{trial.get('title', '')} {json.dumps(trial.get('Criteria', {}))}"[:8000]
        
        vector_values = get_embedding(text_to_embed, nct_id, cached_vectors)
        if not vector_values: continue

        # Standardized Metadata for Reasoning Engine
        metadata = {
            "nct_id": nct_id,
            "title": str(trial.get("title") or ""),
            "min_age": str(trial.get("minimumAge") or "0"),
            # 🛠️ CRITICAL: Named 'structured_criteria' for Reasoning Engine handoff
            "structured_criteria": json.dumps(trial.get("Criteria") or {})
        }

        vectors_to_upsert.append({"id": nct_id, "values": vector_values, "metadata": metadata})

    # Batch Upsert
    BATCH_SIZE = 50
    for i in range(0, len(vectors_to_upsert), BATCH_SIZE):
        batch = vectors_to_upsert[i:i + BATCH_SIZE]
        index.upsert(vectors=batch)
        print(f"✅ Upserted batch {i//BATCH_SIZE + 1}")

    # Save updated catch
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cached_vectors, f, indent=2)

    print(f"✅ Ingestion complete. Credits saved via hashlib content matching.")

if __name__ == "__main__":
    ingest_structured_trials()
