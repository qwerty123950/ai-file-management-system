# backend/services/file_service.py

import os
import sqlite3
from typing import List, Dict, Any

from fastapi import HTTPException
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

# ai package is at the same level as backend
from ai.ocr import extract_text
from ai.embeddings import generate_embedding
from ai.summarizer import summarize_text, summarize_with_sentence_limit
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


def init_qdrant():
    """
    Ensure Qdrant collection 'files' exists with correct vector size and cosine distance.
    """
    # Determine embedding dimension once
    dim = len(generate_embedding("dimension test"))
    try:
        client.get_collection("files")
        print(f"Qdrant collection 'files' already exists.")
    except Exception:
        print(f"Creating Qdrant collection 'files' with dim={dim}")
        client.create_collection(
            collection_name="files",
            vectors_config=VectorParams(
                size=dim,
                distance=Distance.COSINE,
            ),
        )


# Run inits once when this module is imported
init_db()
init_qdrant()


def _split_into_chunks(text: str, max_chars: int = 1000, min_chars: int = 200) -> List[str]:
    """
    Split text into reasonably sized chunks for embedding/search.
    - We try to split on paragraph boundaries first.
    - Each chunk is between min_chars and max_chars where possible.
    """
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        # If adding this paragraph would exceed max_chars, push current as a chunk
        if current and len(current) + len(para) + 2 > max_chars:
            if len(current) >= min_chars or not chunks:
                chunks.append(current.strip())
            else:
                # If current is too small, merge with next anyway
                current = current + "\n\n" + para
                chunks.append(current.strip())
                current = ""
        else:
            current = (current + "\n\n" + para).strip() if current else para

    if current:
        chunks.append(current.strip())

    # Fallback: if still nothing, just return the whole text
    if not chunks:
        return [text]

    return chunks


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
        chunks = []
    else:
        # Use cleaned text if available; otherwise, raw
        content = cleaned if cleaned and cleaned.strip() else raw_content

        # 3) Summarize (stored default = medium)
        try:
            summary = summarize_text(content, mode="medium")
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
            print("[process_file] Empty summary from model, using fallback from content")
            summary = (content[:400] + "...") if len(content) > 400 else content
            summary_type = "fallback"

        embedding_source = content
        chunks = _split_into_chunks(content)

    # 4) Generate embedding for the whole document (optional but useful)
    embedding = generate_embedding(embedding_source)
    print(f"[process_file] doc-level embedding length: {len(embedding)}")

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

    # 6) Store chunk embeddings in Qdrant
    points: List[PointStruct] = []

    # Optional: doc-level point
    points.append(
        PointStruct(
            id=int(file_id),  # numeric id for doc-level
            vector=embedding,
            payload={
                "file_id": file_id,
                "filename": filename,
                "is_doc_level": True,
                "chunk_index": -1,
                "text": summary,  # store summary as doc-level text
            },
        )
    )

    # Chunk-level points
    for idx, chunk_text in enumerate(chunks):
        chunk_emb = generate_embedding(chunk_text)
        # Use string ID to avoid collision with doc-level int IDs
        point_id = f"{file_id}_{idx}"
        points.append(
            PointStruct(
                id=point_id,
                vector=chunk_emb,
                payload={
                    "file_id": file_id,
                    "filename": filename,
                    "is_doc_level": False,
                    "chunk_index": idx,
                    "text": chunk_text,
                },
            )
        )

    if points:
        client.upsert(collection_name="files", points=points)
        print(f"[process_file] Upserted {len(points)} vectors to Qdrant for file_id={file_id}")
    else:
        print("[process_file] No chunks to index in Qdrant")

    return file_id


def _get_file_metadata_map(file_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """
    Fetch filename, summary, summary_type for a list of file_ids from DB.
    Returns a dict: file_id -> metadata dict
    """
    if not file_ids:
        return {}

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in file_ids)
    cursor.execute(
        f"SELECT id, filename, summary, summary_type FROM files WHERE id IN ({placeholders})",
        file_ids,
    )
    rows = cursor.fetchall()
    conn.close()

    meta = {}
    for row in rows:
        meta[row[0]] = {
            "id": row[0],
            "filename": row[1],
            "summary": row[2],
            "summary_type": row[3],
        }
    return meta


def search_files(query, top_k=5):
    """
    Semantic search over chunk embeddings in Qdrant.
    Returns top files, each with:
    - best score
    - stored summary
    - summary_type
    - best matching snippet (chunk)
    """
    query_emb = generate_embedding(query)
    # Search more chunks than final files, to allow grouping
    raw_results = client.search(
        collection_name="files",
        query_vector=query_emb,
        limit=top_k * 5,
        with_payload=True,
    )

    # Aggregate by file_id
    agg: Dict[int, Dict[str, Any]] = {}
    for r in raw_results:
        payload = r.payload or {}
        file_id = payload.get("file_id")
        if file_id is None:
            continue

        score = r.score
        text = payload.get("text", "")
        is_doc_level = payload.get("is_doc_level", False)

        if file_id not in agg or score > agg[file_id]["score"]:
            agg[file_id] = {
                "file_id": file_id,
                "score": score,
                "best_snippet": text,
                "is_doc_level": is_doc_level,
            }

    if not agg:
        return []

    # Get DB metadata for these files
    file_ids = list(agg.keys())
    meta_map = _get_file_metadata_map(file_ids)

    # Merge and sort
    merged: List[Dict[str, Any]] = []
    for fid, info in agg.items():
        meta = meta_map.get(fid)
        if not meta:
            continue
        merged.append(
            {
                "id": fid,
                "score": info["score"],
                "filename": meta["filename"],
                "summary": meta["summary"],
                "summary_type": meta["summary_type"],
                "snippet": info["best_snippet"],
            }
        )

    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged[:top_k]


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


def summarize_file_by_mode(file_id: int, mode: str) -> str:
    """
    Load stored content for a file and generate a fresh summary
    with 1 / 2 / 4 sentences depending on mode.
    """
    if mode not in ("short", "medium", "long"):
        raise HTTPException(status_code=400, detail="Invalid mode")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content, summary_type FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="File not found")

    content, summary_type = row

    if not content or not content.strip():
        # This is an "empty" or placeholder document
        return "No extractable text found in this document."

    if mode == "short":
        sentences = 1
    elif mode == "medium":
        sentences = 2
    else:  # "long"
        sentences = 4

    summary = summarize_with_sentence_limit(content, sentences=sentences)
    if not summary:
        # Fallback to content slice
        summary = (content[:400] + "...") if len(content) > 400 else content

    return summary


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
