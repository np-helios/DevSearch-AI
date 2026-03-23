from fastembed import TextEmbedding

# Load model once
embedding_model = TextEmbedding()

def get_embeddings(texts):
    embeddings = list(embedding_model.embed(texts))
    return embeddings