from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# Initialize Qdrant (local in-memory)
client = QdrantClient(":memory:")

COLLECTION_NAME = "codebase"

def create_collection():
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

def store_embeddings(chunks, embeddings):
    points = []

    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=i,
                vector=vector,
                payload={"text": chunk}
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )