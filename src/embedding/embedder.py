import os
import pickle
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

CACHE_FILE = "embeddings.pkl"

def get_embeddings(chunks):
    if os.path.exists(CACHE_FILE):
        print("Loading cached embeddings...")
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)

    print("Generating embeddings...")
    texts = [chunk["code"] for chunk in chunks]
    embeddings = model.encode(texts)

    with open(CACHE_FILE, "wb") as f:
        pickle.dump(embeddings, f)

    return embeddings