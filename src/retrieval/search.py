from qdrant_client import QdrantClient
from src.embedding.embedder import get_embedding_model
from functools import lru_cache


@lru_cache(maxsize=1)
def get_client():
    return QdrantClient(path="qdrant_data")


model = get_embedding_model()
COLLECTION_NAME = "codebase"
ROLE_HIERARCHY = {
    "employee": {"employee"},
    "manager": {"employee", "manager"},
    "hr": {"employee", "hr"},
    "finance": {"employee", "finance"},
    "legal": {"employee", "legal"},
    "admin": {"employee", "manager", "hr", "finance", "legal", "admin"},
}


def is_authorized(payload, user_role):
    allowed_roles = payload.get("allowed_roles", ["employee"])
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    normalized_role = (user_role or "employee").lower()
    effective_roles = ROLE_HIERARCHY.get(normalized_role, {"employee"})

    return bool(set(role.lower() for role in allowed_roles) & effective_roles)


def search(query, user_role="employee", top_k=5):
    client = get_client()
    query_vector = model.encode(query).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=max(top_k * 4, 10),
    )

    points = results.get("points", []) if isinstance(results, dict) else results.points
    filtered_results = []

    for point in points:
        payload = point.get("payload", {}) if isinstance(point, dict) else getattr(point, "payload", {})
        score = point.get("score", 0) if isinstance(point, dict) else getattr(point, "score", 0)

        if is_authorized(payload, user_role):
            filtered_results.append({
                "score": score,
                "document_id": payload.get("document_id", "unknown"),
                "title": payload.get("title", "Untitled Document"),
                "document_type": payload.get("document_type", "text"),
                "name": payload.get("name", "unknown"),
                "chunk_type": payload.get("chunk_type", "document_section"),
                "content": payload.get("content", ""),
                "path": payload.get("path", "unknown"),
                "summary": payload.get("summary", ""),
                "chunk_index": payload.get("chunk_index", 0),
                "start_line": payload.get("start_line"),
                "end_line": payload.get("end_line"),
                "department": payload.get("department", "general"),
                "classification": payload.get("classification", "internal"),
                "allowed_roles": payload.get("allowed_roles", ["employee"]),
            })

    filtered_results.sort(key=lambda item: item["score"], reverse=True)
    return filtered_results[:top_k]
