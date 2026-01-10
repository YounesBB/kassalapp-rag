import os
import time
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KassalappRAG:
    def __init__(self):
        """Initializes the RAG engine using Pinecone cloud."""
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "kassalapp-index")
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY not found in environment")

        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self.index = self.pc.Index(self.index_name)
        
        # Load embedding model locally with timing
        print("Loading embedding model for retrieval...")
        start_time = time.time()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        duration = time.time() - start_time
        print(f"Model loaded in {duration:.2f} seconds.")

    def query(self, user_query, n_results=3):
        """Retrieves relevant chunks from Pinecone cloud."""
        # 1. Generate embedding for the query
        query_vector = self.model.encode(user_query).tolist()
        
        # 2. Query Pinecone
        results = self.index.query(
            vector=query_vector,
            top_k=n_results,
            include_metadata=True
        )
        
        # 3. Extract text from metadata
        relevant_chunks = []
        for match in results.get("matches", []):
            if "text" in match.get("metadata", {}):
                relevant_chunks.append(match["metadata"]["text"])
        
        return relevant_chunks

if __name__ == "__main__":
    # Test script for Pinecone retrieval
    try:
        rag = KassalappRAG()
        print(f"Connected to Pinecone: {rag.index_name}")
        
        test_query = "What is Trumf?"
        print(f"Testing Query: '{test_query}'")
        
        results = rag.query(test_query)
        if results:
            for i, res in enumerate(results):
                print(f"\n--- Result {i+1} ---")
                print(res)
        else:
            print("No relevant knowledge found in cloud index.")
            
    except Exception as e:
        print(f"Error: {str(e)}")
