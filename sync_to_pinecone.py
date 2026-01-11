"""
Pinecone Synchronization Utility for Kassalapp Assistant.

This script handles the one-time or periodic synchronization of local knowledge files 
(Markdown/Text) to the Pinecone cloud vector database. It handles document chunking, 
embedding generation via SentenceTransformers, and memory-efficient batch upserting.

Usage:
    python sync_to_pinecone.py
"""
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
        raise ValueError("PINECONE_API_KEY not found. Please ensure it is set in your environment or .env file.")

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
        # Wait for index to be ready with a timeout
        print(f"Waiting for index '{PINECONE_INDEX_NAME}' to be ready...")
        max_wait_seconds = 300
        start_time = time.time()
        while not pc.describe_index(PINECONE_INDEX_NAME).status['ready']:
            if time.time() - start_time > max_wait_seconds:
                raise TimeoutError(f"Pinecone index '{PINECONE_INDEX_NAME}' did not become ready within {max_wait_seconds} seconds.")
            time.sleep(1)
            
    return pc.Index(PINECONE_INDEX_NAME)

def chunk_text(text, chunk_size=800):
    """Simple paragraph-based chunking for RAG, with size safety."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        # If the paragraph itself exceeds chunk_size, split it
        if len(p) > chunk_size:
            # Flush current chunk first
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # Split the oversized paragraph into smaller pieces
            temp_p = p
            while len(temp_p) > chunk_size:
                chunks.append(temp_p[:chunk_size].strip())
                temp_p = temp_p[chunk_size:]
            current_chunk = temp_p + "\n\n"
            continue

        if len(current_chunk) + len(p) < chunk_size:
            current_chunk += p + "\n\n"
        else:
            stripped_chunk = current_chunk.strip()
            if stripped_chunk:
                chunks.append(stripped_chunk)
            current_chunk = p + "\n\n"

    if current_chunk:
        stripped_chunk = current_chunk.strip()
        if stripped_chunk:
            chunks.append(stripped_chunk)
    return chunks


def sync():
    """Reads the knowledge folder and prepares vectors for Pinecone."""
    print(f"Reading folder: {KNOWLEDGE_DIR}...")
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"Error: Folder '{KNOWLEDGE_DIR}' not found.")
        return

    index = initialize_pinecone()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    batch = []
    batch_size = 100
    total_vectors = 0
    
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
                record = {
                    "id": f"{filename}_{i}",
                    "values": embedding,
                    "metadata": {
                        "text": chunk,
                        "source": filename
                    }
                }
                batch.append(record)
                total_vectors += 1
                
                # Stream upload if batch is full
                if len(batch) >= batch_size:
                    print(f"Uploading batch of {len(batch)} vectors...")
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            index.upsert(vectors=batch)
                            break
                        except Exception as e:
                            if attempt < max_retries - 1:
                                wait_time = 2 ** attempt
                                print(f"Error uploading batch: {e}. Retrying in {wait_time}s...")
                                time.sleep(wait_time)
                            else:
                                print(f"Failed to upload batch after {max_retries} attempts: {e}")
                                raise
                    batch = []

    # Final upload for remaining vectors
    if batch:
        print(f"Uploading final batch of {len(batch)} vectors...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                index.upsert(vectors=batch)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Error uploading final batch: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Failed to upload final batch after {max_retries} attempts: {e}")
                    raise
    
    if total_vectors > 0:
        print(f"Sync Complete! Total vectors processed: {total_vectors}")
    else:
        print("No markdown or text files found to sync.")

if __name__ == "__main__":
    try:
        sync()
    except Exception as e:
        print(f"Error: {str(e)}")
