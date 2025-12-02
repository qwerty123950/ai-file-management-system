# backend/services/file_service.py

import os
import sqlite3

from fastapi import HTTPException
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# ai package is at the same level as backend
from ai.ocr import extract_text
from ai.embeddings import generate_embedding
from ai.summarizer import summarize_text
from ai.deduplication import is_duplicate  # even if unused for now
from ai.preprocess import clean_text

# Make the DB path absolute and consistent
DATABASE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "database", "database.db")
)
QDRANT_URL = "http://localhost:6333"  # Assuming local Qdrant

client = QdrantClient(url=QDRANT_URL)


def init_db():
    """Create the database directory and files table if they don't exist."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            content TEXT,
            summary TEXT,
            summary_type TEXT
        );
        """
    )

    conn.commit()
    conn.close()
    print("DB initialized at:", DATABASE_PATH)


# Run init once when this module is imported
init_db()


def process_file(file_path, filename):
    print(f"[process_file] Starting for {filename} at {file_path}")

    # 1) Extract text
    raw_content = extract_text(file_path)
    print(f"[process_file] raw_content length: {len(raw_content) if raw_content else 0}")

    if raw_content == "Unsupported file type":
        print("[process_file] Unsupported file type, aborting.")
        return None

    # 2) Clean / normalize text
    cleaned = clean_text(raw_content)
    print(f"[process_file] cleaned content length: {len(cleaned) if cleaned else 0}")

    # Detect if we actually have any real text
    has_real_text = bool(cleaned and cleaned.strip()) or bool(
        raw_content and raw_content.strip()
    )

    if not has_real_text:
        # Nothing meaningful to summarize
        print("[process_file] No extractable text, using placeholder summary")
        content = ""  # store empty content
        summary = "No extractable text found in this document."
        summary_type = "placeholder"
        embedding_source = "empty document"
    else:
        # Use cleaned text if available; otherwise, raw
        content = cleaned if cleaned and cleaned.strip() else raw_content

        # 3) Summarize (with error handling)
        try:
            summary = summarize_text(content)
            if summary is None:
                summary = ""
            summary = summary.strip()
            print(f"[process_file] summary length after strip: {len(summary)}")
        except Exception as e:
            print("Summarization error:", repr(e))
            raise HTTPException(status_code=500, detail="Error while summarizing file")

        if summary:
            summary_type = "ai"
        else:
            # Fallback: if summarizer returns nothing, use the first part of the content
            print("[process_file] Empty summary from model, using fallback from content")
            summary = (content[:400] + "...") if len(content) > 400 else content
            summary_type = "fallback"

        embedding_source = content

    # 4) Generate embedding
    embedding = generate_embedding(embedding_source)
    print(f"[process_file] embedding length: {len(embedding)}")

    # 5) Store in SQLite DB
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO files (filename, filepath, content, summary, summary_type) "
        "VALUES (?, ?, ?, ?, ?)",
        (filename, file_path, content, summary, summary_type),
    )
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"[process_file] Stored file in DB with id={file_id}")

    # 6) Store in Qdrant
    point = PointStruct(
        id=file_id,
        vector=embedding,
        payload={
            "filename": filename,
            "summary": summary,
            "summary_type": summary_type,
        },
    )
    client.upsert(collection_name="files", points=[point])

    print(f"[process_file] Upserted vector to Qdrant for id={file_id}")

    return file_id


def search_files(query, top_k=5):
    query_emb = generate_embedding(query)
    results = client.search(
        collection_name="files",
        query_vector=query_emb,
        limit=top_k,
    )
    return [
        {
            "id": r.id,
            "score": r.score,
            "filename": r.payload.get("filename"),
            "summary": r.payload.get("summary"),
            "summary_type": r.payload.get("summary_type"),
        }
        for r in results
    ]


def get_all_files():
    """Return all files stored in the DB."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, filepath, summary, summary_type "
        "FROM files ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "filename": row[1],
            "filepath": row[2],
            "summary": row[3],
            "summary_type": row[4],
        }
        for row in rows
    ]


def check_duplicates(file_id):
    """
    Placeholder for duplicate check. Later, you can:
    - Use Qdrant similarity search on the new file's embedding
    - Compare top result score with a threshold
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM files WHERE id != ?", (file_id,))
    other_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not other_ids:
        return []

    duplicates = []
    # TODO: implement using Qdrant search + is_duplicate threshold
    for oid in other_ids:
        pass

    return duplicates
