import os
import sys
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv()

def flush_pinecone_index():
    """
    Part of the Data Engineering Team action plan: 
    Ensures a clean state for high-precision Hybrid RAG testing.
    """
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX")

    # 1. Validation Check
    if not api_key or not index_name:
        print("❌ ERROR: Missing Pinecone credentials in .env file.")
        sys.exit(1)

    try:
        # 2. Initialize Connection
        print(f"📡 Connecting to Pinecone index: {index_name}...")
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)

        # 3. Fetch Stats before deletion
        stats_before = index.describe_index_stats()
        total_vectors = stats_before['total_vector_count']
        
        if total_vectors == 0:
            print(f"ℹ️  Index '{index_name}' is already empty. No action needed.")
            return

        # 4. Perform Wipe
        print(f"🧹 Deleting {total_vectors} vectors from '{index_name}'...")
        index.delete(delete_all=True)
        
        # 5. Final Confirmation
        print("✨ SUCCESS: Index is now empty and ready for fresh ingestion.")
        print("💡 Note: It may take up to 60 seconds for the dashboard to reflect 0 vectors.")

    except Exception as e:
        print(f"❌ CRITICAL ERROR during flush: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    flush_pinecone_index()
