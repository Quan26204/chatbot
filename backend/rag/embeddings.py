from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


print(f"Loading embedding model: {MODEL_NAME}")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded.")


def create_embeddings(texts):
    """
    Convert a list of text chunks into embeddings.
    """

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    return embeddings