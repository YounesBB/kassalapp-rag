import os
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
# Using a simple line-based or paragraph-based chunking for now.

class KassalappRAG:
    def __init__(self, collection_name="kassalapp_docs", persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use a local embedding function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def chunk_text(self, text, chunk_size=1000, chunk_overlap=200):
        """Simple paragraph-based chunking for markdown."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) < chunk_size:
                current_chunk += p + "\n\n"
            else:
                chunks.append(current_chunk.strip())
                # Overlap: keep some context
                current_chunk = p + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    def index_file(self, file_path):
        """Indexes a single markdown file."""
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        chunks = self.chunk_text(content)
        ids = [f"{os.path.basename(file_path)}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": file_path} for _ in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Indexed {len(chunks)} chunks from {file_path}")

    def query(self, user_query, n_results=3):
        """Retrieves relevant chunks for a query."""
        results = self.collection.query(
            query_texts=[user_query],
            n_results=n_results
        )
        return results["documents"][0] if results["documents"] else []

if __name__ == "__main__":
    # Test script
    rag = KassalappRAG()
    knowledge_path = "knowledge/expert_guide.md"
    if os.path.exists(knowledge_path):
        rag.index_file(knowledge_path)
        print("Query Test: 'What is Trumf?'")
        print(rag.query("What is Trumf?"))
