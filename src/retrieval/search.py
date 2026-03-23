from src.vectorstore.qdrant_store import client, COLLECTION_NAME
from src.embedding.embedder import get_embeddings

def search(query):
    query_embedding = get_embeddings([query])[0]

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=3
    )

    return [point.payload["text"] for point in results.points]