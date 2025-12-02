# create_qdrant_collection.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(url="http://localhost:6333")

# all-MiniLM-L6-v2 has 384 dimensions
client.recreate_collection(
    collection_name="files",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

print("Collection 'files' created.")