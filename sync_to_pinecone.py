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

def chunk_text(text, chunk_size=800):
    """Simple paragraph-based chunking for RAG."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) < chunk_size:
            current_chunk += p + "\n\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

if __name__ == "__main__":
    try:
        # TEST 1: Connection
        index = initialize_pinecone()
        print(f"✅ Connected to Pinecone index: {PINECONE_INDEX_NAME}")

        # TEST 2: Chunking
        test_text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        chunks = chunk_text(test_text, chunk_size=20)
        print(f"✅ Chunking logic test: Created {len(chunks)} chunks.")

        # TEST 3: Embedding
        print("⏳ Loading embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        test_embedding = model.encode("How much is milk?").tolist()
        print(f"✅ Embedding logic test: Vector length is {len(test_embedding)}.")

        # TEST 4: Batch Upsert Example with dummy data)
        print("⏳ Testing batch upsert logic...")
        # Create some dummy vectors for testing upsert
        dummy_vectors = []
        for i in range(5): # Create 5 dummy vectors
            vec_id = f"test_vec_{i}"
            vec_data = model.encode(f"This is a test sentence number {i}.").tolist()
            dummy_vectors.append({"id": vec_id, "values": vec_data, "metadata": {"source": "test_data"}})

        if dummy_vectors:
            print(f"📤 Uploading {len(dummy_vectors)} vectors to Pinecone in batches...")
            # Batch upsert is safer for large datasets
            batch_size = 2
            for i in range(0, len(dummy_vectors), batch_size):
                batch = dummy_vectors[i:i + batch_size]
                index.upsert(vectors=batch)
            print("✅ Batch upsert test complete!")
        else:
            print("⚠️ No dummy vectors created for upsert test.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
