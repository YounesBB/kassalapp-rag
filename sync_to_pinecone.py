import os
import time
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "kassalapp-index")
KNOWLEDGE_DIR = "knowledge"

def initialize_pinecone():
    """Initializes Pinecone and ensures the index exists."""
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not found in .env")

    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Check if index exists, create if not
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"🚀 Creating new index: {PINECONE_INDEX_NAME}...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=384, # Dimension for all-MiniLM-L6-v2
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1' # free tier region
            )
        )
        # Wait for index to be ready
        while not pc.describe_index(PINECONE_INDEX_NAME).status['ready']:
            time.sleep(1)
            
    return pc.Index(PINECONE_INDEX_NAME)

if __name__ == "__main__":
    try:
        index = initialize_pinecone()
        print(f"✅ Connected to Pinecone index: {PINECONE_INDEX_NAME}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
