import requests

BACKEND_URL = "http://localhost:8000"

# Test upload
with open("sample_docs/sample_text.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BACKEND_URL}/api/upload", files=files)
    print("Upload response:", response.json())

# Test search
query = "sample text content"
response = requests.get(f"{BACKEND_URL}/api/search", params={"query": query})
print("Search response:", response.json())