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
        print(f" Creating new index: {PINECONE_INDEX_NAME}...")
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
def sync():
    """Reads the knowledge folder and prepares vectors for Pinecone."""
    print(f"Reading folder: {KNOWLEDGE_DIR}...")
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"Error: Folder '{KNOWLEDGE_DIR}' not found.")
        return

    index = initialize_pinecone()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    vectors = []
    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.endswith(".md") or filename.endswith(".txt"):
            file_path = os.path.join(KNOWLEDGE_DIR, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            chunks = chunk_text(content)
            print(f"Processing {filename} ({len(chunks)} chunks)...")
            
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = model.encode(chunk).tolist()
                
                # Prepare the record
                vectors.append({
                    "id": f"{filename}_{i}",
                    "values": embedding,
                    "metadata": {
                        "text": chunk,
                        "source": filename
                    }
                })

    if vectors:
        print(f"Uploading {len(vectors)} vectors to Pinecone...")
        # Batch upsert is safer for large datasets
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            index.upsert(vectors=batch)
        print("Sync Complete!")
    else:
        print("No markdown or text files found to sync.")

if __name__ == "__main__":
    try:
        sync()
    except Exception as e:
        print(f"Error: {str(e)}")
