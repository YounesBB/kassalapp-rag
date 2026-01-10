import os
import time
import streamlit as st
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KassalappRAG:
    def __init__(self):
        """Initializes the RAG engine using Pinecone cloud."""
        # Universal Secrets: Try Streamlit Secrets (Cloud), then Environment Variables (Local)
        # We wrap this in a safe check to avoid crashes when running as a standalone script
        try:
            self.api_key = st.secrets.get("PINECONE_API_KEY") or os.getenv("PINECONE_API_KEY")
            self.index_name = st.secrets.get("PINECONE_INDEX_NAME") or os.getenv("PINECONE_INDEX_NAME")
        except (AttributeError, RuntimeError):
            # Fallback for local execution outside of Streamlit
            self.api_key = os.getenv("PINECONE_API_KEY")
            self.index_name = os.getenv("PINECONE_INDEX_NAME")
            
        # Ensure consistent default for index name
        if not self.index_name:
            self.index_name = "kassalapp-index"
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY not found. Please set it as a Secret or Environment Variable.")

        # Initialize Pinecone and verify index connection
        self.pc = Pinecone(api_key=self.api_key)
        try:
            # Check if index exists by listing names (proactive check)
            if self.index_name not in self.pc.list_indexes().names():
                raise ValueError(f"Index '{self.index_name}' not found.")
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            raise RuntimeError(
                f"Unable to connect to Pinecone index '{self.index_name}'. "
                "Ensure you have run 'sync_to_pinecone.py' first to initialize the cloud database."
            ) from e
        
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
        try:
            results = self.index.query(
                vector=query_vector,
                top_k=n_results,
                include_metadata=True
            )
        except Exception as e:
            print(f"Error querying Pinecone index '{self.index_name}': {e}")
            return []
        
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
