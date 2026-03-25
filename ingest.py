import sys
import os

sys.path.append(os.path.abspath("."))

from src.ingestion.loader import load_codebase
from src.ingestion.chunker import chunk_python_file
from src.embedding.embedder import get_embeddings
from src.vectorstore.qdrant_store import create_collection, store_embeddings


def run_ingestion():
    print("🚀 Starting ingestion pipeline...\n")

    # 🔥 CHANGE THIS PATH
    REPO_PATH = "data"   # <-- put your code files here

    # 1️⃣ Load code
    print("📂 Loading codebase...")
    docs = load_codebase(REPO_PATH)
    print(f"Loaded {len(docs)} files\n")

    # 2️⃣ Chunking
    print("✂️ Chunking code...")
    all_chunks = []

    for doc in docs:
        file_content = doc["content"]   # ✅ FIXED KEY

        chunks = chunk_python_file(file_content)

        for chunk in chunks:
            chunk["department"] = "engineering"   # example
            chunk["access_level"] = "employee"    # employee / manager / admin
            all_chunks.append(chunk)

    print(f"Created {len(all_chunks)} chunks\n")

    # 3️⃣ Embedding
    print("🧠 Generating embeddings...")
    embeddings = get_embeddings(all_chunks)   # ✅ FIXED FUNCTION

    print(f"Generated {len(embeddings)} embeddings\n")

    # 4️⃣ Store in Qdrant
    print("💾 Storing in Qdrant...")
    create_collection()
    store_embeddings(all_chunks, embeddings)

    print("\n✅ Ingestion completed successfully!")


if __name__ == "__main__":
    run_ingestion()