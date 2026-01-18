# backend/services/file_service.py

import os
import sqlite3
import re
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

# ai package is at the same level as backend
from ai.ocr import extract_text
from ai.embeddings import generate_embedding
from ai.summarizer import summarize_text, summarize_with_sentence_limit
from ai.deduplication import is_duplicate  # kept even if unused
from ai.preprocess import clean_text
from ai.tagger import generate_tags


# -------------------------------------------------------------------
# Paths & clients
# -------------------------------------------------------------------

DATABASE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "database", "database.db")
)

QDRANT_URL = "http://localhost:6333"
client = QdrantClient(url=QDRANT_URL, prefer_grpc=False)


# -------------------------------------------------------------------
# DB & Qdrant init
# -------------------------------------------------------------------

def ensure_db() -> None:
    """Ensure SQLite DB and table exist."""
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
            summary_type TEXT,
            tags TEXT
        );
        """
    )

    cursor.execute("PRAGMA table_info(files)")
    cols = [row[1] for row in cursor.fetchall()]
    if "tags" not in cols:
        cursor.execute("ALTER TABLE files ADD COLUMN tags TEXT")

    conn.commit()
    conn.close()


def init_db() -> None:
    ensure_db()
    print("DB initialized at:", DATABASE_PATH)


def init_qdrant() -> None:
    """Ensure Qdrant collection exists."""
    dim = len(generate_embedding("dimension test"))

    try:
        client.get_collection("files")
        print("Qdrant collection 'files' already exists.")
    except Exception:
        print(f"Creating Qdrant collection 'files' with dim={dim}")
        client.create_collection(
            collection_name="files",
            vectors_config=VectorParams(
                size=dim,
                distance=Distance.COSINE,
            ),
        )


# Run once on import
init_db()
init_qdrant()


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _split_into_chunks(
    text: str, max_chars: int = 1000, min_chars: int = 200
) -> List[str]:
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        if current and len(current) + len(para) > max_chars:
            chunks.append(current.strip())
            current = para
        else:
            current = f"{current}\n\n{para}".strip() if current else para

    if current:
        chunks.append(current.strip())

    return chunks or [text]


def _get_file_metadata_map(file_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    if not file_ids:
        return {}

    ensure_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    placeholders = ",".join("?" for _ in file_ids)
    cursor.execute(
        f"SELECT id, filename, summary, summary_type FROM files WHERE id IN ({placeholders})",
        file_ids,
    )

    rows = cursor.fetchall()
    conn.close()

    return {
        r[0]: {
            "id": r[0],
            "filename": r[1],
            "summary": r[2],
            "summary_type": r[3],
        }
        for r in rows
    }


def _count_word_occurrences(text: str, word: str) -> int:
    if not text or not word:
        return 0
    pattern = re.compile(rf"\b{re.escape(word.lower())}\b")
    return len(pattern.findall(text.lower()))


# -------------------------------------------------------------------
# Core: process_file
# -------------------------------------------------------------------

def process_file(file_path: str, filename: str) -> Optional[int]:
    raw_content = extract_text(file_path)

    if raw_content == "Unsupported file type":
        return None

    cleaned = clean_text(raw_content)

    has_real_text = bool(cleaned and cleaned.strip()) or bool(raw_content and raw_content.strip())

    if not has_real_text:
        content = ""
        summary = "No extractable text found in this document."
        summary_type = "placeholder"
        chunks: List[str] = []
        tags_str = ""
    else:
        content = cleaned if cleaned.strip() else raw_content

        # ---------------- SAFE SUMMARY ----------------
        try:
            # Hard limit to avoid Pegasus crash
            summary_input = content[:1800]
            summary = summarize_text(summary_input, mode="medium") or ""
            summary = summary.strip()
            if not summary:
                raise ValueError("empty summary")
            summary_type = "ai"
        except Exception:
            summary = (content[:400] + "...") if len(content) > 400 else content
            summary_type = "fallback"

        chunks = _split_into_chunks(content)
        tags_str = ", ".join(generate_tags(summary or content))

    # ---------------- SAFE EMBEDDING ----------------
    try:
        # HARD limit embedding input
        embedding_input = content[:2000] if content else "empty document"
        embedding = generate_embedding(embedding_input)
    except Exception:
        embedding = generate_embedding("empty document")

    # ---------------- DB INSERT ----------------
    ensure_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO files (filename, filepath, content, summary, summary_type, tags)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (filename, file_path, content, summary, summary_type, tags_str),
    )

    file_id = cursor.lastrowid
    if file_id is None:
        conn.close()
        raise RuntimeError("Failed to insert file into database")

    conn.commit()
    conn.close()

    # ---------------- QDRANT ----------------
    points: List[PointStruct] = [
        PointStruct(
            id=int(file_id),
            vector=embedding,
            payload={
                "file_id": file_id,
                "filename": filename,
                "is_doc_level": True,
                "chunk_index": -1,
                "text": summary,
            },
        )
    ]

    for idx, chunk in enumerate(chunks):
        try:
            chunk_emb = generate_embedding(chunk[:2000])
        except Exception:
            continue

        points.append(
            PointStruct(
                id=file_id * 10_000 + idx,
                vector=chunk_emb,
                payload={
                    "file_id": file_id,
                    "filename": filename,
                    "is_doc_level": False,
                    "chunk_index": idx,
                    "text": chunk,
                },
            )
        )

    if points:
        client.upsert(collection_name="files", points=points)

    return file_id


# -------------------------------------------------------------------
# Search / list / tag / reindex / delete
# -------------------------------------------------------------------

def search_files(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    query_emb = generate_embedding(query)

    results = client.query_points(
        collection_name="files",
        prefetch=[],
        query=query_emb,
        limit=top_k * 5,
        with_payload=True,
    ).points


    agg: Dict[int, Dict[str, Any]] = {}

    for r in results:
        payload = r.payload or {}

        fid_raw = payload.get("file_id")
        if fid_raw is None:
            continue

        fid = int(fid_raw)

        score = r.score
        text = payload.get("text", "")

        if fid not in agg or score > agg[fid]["score"]:
            agg[fid] = {
                "score": score,
                "snippet": text,
            }

    meta = _get_file_metadata_map(list(agg.keys()))

    merged = [
        {
            "id": fid,
            "score": v["score"],
            "filename": meta[fid]["filename"],
            "summary": meta[fid]["summary"],
            "summary_type": meta[fid]["summary_type"],
            "snippet": v["snippet"],
        }
        for fid, v in agg.items()
        if fid in meta
    ]

    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged[:top_k]


def get_all_files() -> List[Dict[str, Any]]:
    ensure_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, filename, filepath, summary, summary_type, tags FROM files ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "filename": r[1],
            "filepath": r[2],
            "summary": r[3],
            "summary_type": r[4],
            "tags": r[5],
        }
        for r in rows
    ]


def get_files_by_tag(tag: str) -> List[Dict[str, Any]]:
    ensure_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, filename, filepath, summary, summary_type, tags
        FROM files
        WHERE lower(tags) LIKE ?
        """,
        (f"%{tag.lower()}%",),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "filename": r[1],
            "filepath": r[2],
            "summary": r[3],
            "summary_type": r[4],
            "tags": r[5],
        }
        for r in rows
    ]


def delete_file(file_id: int) -> Dict[str, Any]:
    ensure_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT filename FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="File not found")

    filename = row[0]
    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    client.delete(
        collection_name="files",
        points_selector=Filter(
            must=[FieldCondition(key="file_id", match=MatchValue(value=file_id))]
        ),
    )

    return {"id": file_id, "filename": filename}


def reindex_all_files() -> Dict[str, Any]:
    ensure_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, filename, filepath, content, summary, summary_type FROM files"
    )
    rows = cursor.fetchall()
    conn.close()

    client.delete_collection("files")
    init_qdrant()

    points: List[PointStruct] = []

    for fid, filename, _, content, summary, _ in rows:
        emb_src = content if content else "empty document"
        chunks = _split_into_chunks(content) if content else []

        points.append(
            PointStruct(
                id=fid,
                vector=generate_embedding(emb_src),
                payload={
                    "file_id": fid,
                    "filename": filename,
                    "is_doc_level": True,
                    "chunk_index": -1,
                    "text": summary or "",
                },
            )
        )

        for idx, chunk in enumerate(chunks):
            points.append(
                PointStruct(
                    id=fid * 10_000 + idx,
                    vector=generate_embedding(chunk),
                    payload={
                        "file_id": fid,
                        "filename": filename,
                        "is_doc_level": False,
                        "chunk_index": idx,
                        "text": chunk,
                    },
                )
            )

    for i in range(0, len(points), 64):
        client.upsert(collection_name="files", points=points[i:i + 64])

    return {"reindexed": len(rows)}

# -------------------------------------------------------------------
# Missing functions required by routes/files.py
# -------------------------------------------------------------------

def summarize_file_by_mode(file_id: int, mode: str) -> str:
    ensure_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content, summary FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "File not found."

    content, stored_summary = row

    if not content or not content.strip():
        return stored_summary or "No content available."

    # ---------------------------------------
    # HARD SAFETY LIMITS (Pegasus-safe)
    # ---------------------------------------
    if mode == "short":
        max_chars = 600
    elif mode == "medium":
        max_chars = 1200
    elif mode == "long":
        max_chars = 1800   # 🚨 DO NOT EXCEED THIS
    else:
        max_chars = 1200

    safe_text = content[:max_chars]

    try:
        summary = summarize_text(safe_text, mode=mode)
        if summary and summary.strip():
            return summary.strip()
    except Exception:
        pass

    # ---------------------------------------
    # FINAL FALLBACK (never crash API)
    # ---------------------------------------
    fallback = content[:400]
    if len(content) > 400:
        fallback += "..."
    return fallback



def find_similar_files(file_id: int, top_k: int = 5) -> List[Dict[str, Any]]:
    ensure_db()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        return []

    query_emb = generate_embedding(row[0])

    results = client.query_points(
        collection_name="files",
        prefetch=[],
        query=query_emb,
        limit=top_k * 5,
        with_payload=True,
    ).points

    seen = set()
    candidates = []

    for r in results:
        payload = r.payload or {}
        fid = payload.get("file_id")

        if fid is None or fid == file_id or fid in seen:
            continue

        seen.add(fid)
        candidates.append(
            {
                "file_id": fid,
                "score": r.score,
            }
        )

        if len(candidates) >= top_k:
            break

    if not candidates:
        return []

    # 🔑 fetch metadata so frontend has what it needs
    meta_map = _get_file_metadata_map([c["file_id"] for c in candidates])

    output: List[Dict[str, Any]] = []

    for c in candidates:
        fid = c["file_id"]
        meta = meta_map.get(fid)
        if not meta:
            continue

        output.append(
            {
                "id": fid,                         # ✅ frontend expects this
                "filename": meta["filename"],      # ✅ frontend expects this
                "summary": meta["summary"],
                "summary_type": meta["summary_type"],
                "score": c["score"],
            }
        )

    return output


def check_duplicates(file_id: int, threshold: float = 0.9) -> Dict[str, Any]:
    """
    Return files that are very similar to the given file (potential duplicates).
    Includes current file info + duplicate file id & filename.
    """

    ensure_db()

    # fetch current file info
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    current_filename = row[0]

    similar = find_similar_files(file_id, top_k=20)

    # filter by similarity threshold
    duplicates = [
        {
            "id": s["id"],
            "filename": s["filename"],
            "score": s["score"],
        }
        for s in similar
        if s["score"] >= threshold
    ]

    return {
        "current_file": {
            "id": file_id,
            "filename": current_filename,
        },
        "duplicates": duplicates,
    }



def search_file_by_word(word: str) -> Optional[Dict[str, Any]]:
    if not word:
        return None

    ensure_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, filepath, content FROM files"
    )
    rows = cursor.fetchall()
    conn.close()

    best = None
    best_count = 0

    for fid, fname, fpath, content in rows:
        if not content:
            continue
        count = _count_word_occurrences(content, word)
        if count > best_count:
            best_count = count
            best = (fid, fname, fpath, content)

    if not best:
        return None

    return {
        "id": best[0],
        "filename": best[1],
        "filepath": best[2],
        "content": best[3],
        "count": best_count,
    }


def search_file_by_word_count(query: str) -> Optional[Dict[str, Any]]:
    return search_file_by_word(query)
