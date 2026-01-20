# ai/embeddings.py
import os

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HOME"] = os.path.expanduser("~/.cache/huggingface")
os.environ["TRANSFORMERS_CACHE"] = os.path.expanduser("~/.cache/huggingface")


from typing import List
from sentence_transformers import SentenceTransformer

# Light, fast, strong general-purpose embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(
    EMBEDDING_MODEL_NAME, 
    local_files_only=True
)

def generate_embedding(text: str) -> List[float]:
    """
    Generate a single embedding vector for a piece of text.
    """
    if not text:
        text = ""
    emb = model.encode(text, normalize_embeddings=True)
    return emb.tolist()
