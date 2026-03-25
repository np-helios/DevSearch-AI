from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient(path="qdrant_data")
model = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME = "codebase"


def search(query, user_role="employee", top_k=5):
    query_vector = model.encode(query).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    )

    filtered_results = []

    # ✅ Handle both formats safely
    points = results.get("points", []) if isinstance(results, dict) else results.points

    for r in points:
        # ✅ Extract payload safely
        if isinstance(r, dict):
            payload = r.get("payload", {})
        else:
            payload = getattr(r, "payload", {})

        access_level = payload.get("access_level", "employee")

        # RBAC filtering
        if user_role == "admin":
            filtered_results.append(payload)
        elif user_role == access_level:
            filtered_results.append(payload)

    return filtered_results