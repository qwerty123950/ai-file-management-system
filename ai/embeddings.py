# ai/embeddings.py

from typing import List
from sentence_transformers import SentenceTransformer

# Light, fast, strong general-purpose embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def generate_embedding(text: str) -> List[float]:
    """
    Generate a single embedding vector for a piece of text.
    """
    if not text:
        text = ""
    emb = _model.encode(text, normalize_embeddings=True)
    return emb.tolist()
