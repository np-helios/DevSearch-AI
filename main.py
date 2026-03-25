from src.ingestion.loader import load_codebase
from src.ingestion.chunker import chunk_python_file
from src.embedding.embedder import get_embeddings
from src.vectorstore.qdrant_store import create_collection, store_embeddings
from src.retrieval.search import search
from src.llm.llm import generate_answer


if __name__ == "__main__":
    repo_path = "./"

    files = load_codebase(repo_path)

    all_chunks = []

    for file in files:
        chunks = chunk_python_file(file["content"])
        all_chunks.extend(chunks)

    all_chunks = all_chunks[:2000]

    print(f"Total chunks: {len(all_chunks)}")

    create_collection()

    embeddings = get_embeddings(all_chunks)

    store_embeddings(all_chunks, embeddings)

    print("Embeddings stored successfully!")

    while True:
        query = input("\nAsk a question (or 'exit'): ")

        if query.lower() == "exit":
            break

        results = search(query)

        print("\nTop Matches:\n")
        for r in results:
            print(f"Function/Class: {r.payload['name']}")
            print(r.payload["code"][:200])
            print("-" * 50)

        answer = generate_answer(query, results)

        print("\nFinal Answer:\n")
        print(answer)