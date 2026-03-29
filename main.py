from src.ingestion.loader import load_documents
from src.ingestion.chunker import chunk_document
from src.embedding.embedder import get_embeddings
from src.vectorstore.qdrant_store import create_collection, store_embeddings
from src.retrieval.search import search
from src.llm.llm import generate_answer


if __name__ == "__main__":
    repo_path = "./data"

    documents = load_documents(repo_path)

    all_chunks = []

    for document in documents:
        chunks = chunk_document(document)
        all_chunks.extend(chunks)

    all_chunks = all_chunks[:2000]

    print(f"Total chunks: {len(all_chunks)}")

    create_collection()

    embeddings = get_embeddings(all_chunks)

    store_embeddings(all_chunks, embeddings)

    print("Embeddings stored successfully!")

    while True:
        query = input("\nAsk a question (or 'exit'): ")
        role = input("Role (employee/manager/hr/finance/legal/admin): ").strip().lower() or "employee"

        if query.lower() == "exit":
            break

        results = search(query, user_role=role)

        print("\nTop Matches:\n")
        for r in results:
            print(f"Document: {r['title']}")
            print(f"Section: {r['name']} ({r['chunk_type']})")
            print(f"Path: {r['path']}")
            print(r["content"][:200])
            print("-" * 50)

        answer = generate_answer(query, results)

        print("\nFinal Answer:\n")
        print(answer)
