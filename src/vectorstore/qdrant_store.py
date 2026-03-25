from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

client = QdrantClient(path="qdrant_data")

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
                vector=vector.tolist(),
                payload={
                    "code": chunk["code"],
                    "name": chunk["name"],
                    "type": chunk["type"],
                    "department": chunk.get("department", "general"),
                    "access_level": chunk.get("access_level", "employee")
                }
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)