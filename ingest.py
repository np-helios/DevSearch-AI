import sys
import os

sys.path.append(os.path.abspath("."))

from src.ingestion.loader import load_documents
from src.ingestion.chunker import chunk_document
from src.embedding.embedder import get_embeddings
from src.vectorstore.qdrant_store import create_collection, store_embeddings


def run_ingestion():
    print("Starting ingestion pipeline...\n")

    repo_path = "data"

    print("Loading company documents...")
    docs = load_documents(repo_path)
    print(f"Loaded {len(docs)} documents\n")

    print("Chunking documents...")
    all_chunks = []

    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

    print(f"Created {len(all_chunks)} chunks\n")

    print("Generating embeddings...")
    embeddings = get_embeddings(all_chunks)
    print(f"Generated {len(embeddings)} embeddings\n")

    print("Storing in Qdrant...")
    create_collection()
    store_embeddings(all_chunks, embeddings)

    print("\nIngestion completed successfully!")


if __name__ == "__main__":
    run_ingestion()
