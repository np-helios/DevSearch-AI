import hashlib
import math
import os
import re

EMBEDDING_DIMENSION = 384
TOKEN_PATTERN = re.compile(r"\b\w+\b")


class LocalHashingEmbedder:
    def __init__(self, dimension=EMBEDDING_DIMENSION):
        self.dimension = dimension

    def _encode_text(self, text):
        vector = [0.0] * self.dimension
        tokens = TOKEN_PATTERN.findall((text or "").lower())

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]

        return vector

    def encode(self, texts):
        if isinstance(texts, str):
            return self._encode_text(texts)
        return [self._encode_text(text) for text in texts]


def _load_model():
    if os.getenv("USE_LOCAL_HASH_EMBEDDER", "").lower() in {"1", "true", "yes"}:
        print("Using offline hashing embeddings by configuration.")
        return LocalHashingEmbedder()

    try:
        from sentence_transformers import SentenceTransformer

        print("Using sentence-transformers embeddings.")
        return SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception as exc:
        print(f"Falling back to offline hashing embeddings: {exc}")
        return LocalHashingEmbedder()


model = _load_model()


def get_embedding_model():
    return model


def get_embeddings(chunks):
    print("Generating embeddings...")
    texts = [chunk["content"] for chunk in chunks]
    return model.encode(texts)
