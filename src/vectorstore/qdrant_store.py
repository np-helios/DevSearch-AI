from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from functools import lru_cache

COLLECTION_NAME = "codebase"


@lru_cache(maxsize=1)
def get_client():
    return QdrantClient(path="qdrant_data")


def create_collection():
    get_client().recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )


def store_embeddings(chunks, embeddings):
    points = []

    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        serialized_vector = vector.tolist() if hasattr(vector, "tolist") else list(vector)
        points.append(
            PointStruct(
                id=i,
                vector=serialized_vector,
                payload={
                    "document_id": chunk["document_id"],
                    "title": chunk["title"],
                    "document_type": chunk["document_type"],
                    "content": chunk["content"],
                    "name": chunk["name"],
                    "chunk_type": chunk["chunk_type"],
                    "path": chunk.get("path", "unknown"),
                    "summary": chunk.get("summary", ""),
                    "chunk_index": chunk.get("chunk_index", 0),
                    "start_line": chunk.get("start_line"),
                    "end_line": chunk.get("end_line"),
                    "department": chunk.get("department", "general"),
                    "classification": chunk.get("classification", "internal"),
                    "allowed_roles": chunk.get("allowed_roles", ["employee"]),
                },
            )
        )

    get_client().upsert(collection_name=COLLECTION_NAME, points=points)
