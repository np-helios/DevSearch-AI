from src.ingestion.loader import load_codebase
from src.ingestion.chunker import chunk_python_file

from src.embedding.embedder import get_embeddings
from src.vectorstore.qdrant_store import create_collection, store_embeddings
from src.retrieval.search import search


if __name__ == "__main__":
    repo_path = "./"

    # Load files
    files = load_codebase(repo_path)

    all_chunks = []

    # Chunk files
    for file in files:
        chunks = chunk_python_file(file["content"])
        all_chunks.extend(chunks)

    # 🔥 LIMIT CHUNKS (VERY IMPORTANT)
    MAX_CHUNKS = 2000
    all_chunks = all_chunks[:MAX_CHUNKS]

    print(f"Total chunks after limit: {len(all_chunks)}")

    # Create vector DB
    create_collection()

    # Generate embeddings
    embeddings = get_embeddings(all_chunks)

    # Store in Qdrant
    store_embeddings(all_chunks, embeddings)

    print("Embeddings stored successfully!")

    # 🔍 Query loop
    while True:
        query = input("\nAsk a question (or 'exit'): ")

        if query.lower() == "exit":
            break

        results = search(query)

        print("\nTop Results:")
        for i, res in enumerate(results):
            print(f"\nResult {i+1}:\n{res}")