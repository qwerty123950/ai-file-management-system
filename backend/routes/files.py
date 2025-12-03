# backend/routes/files.py

from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os

from backend.services.file_service import (
    process_file,
    search_files,
    get_all_files,
    summarize_file_by_mode,
    find_similar_files,
    check_duplicates,
    delete_file,
    reindex_all_files,
)

router = APIRouter()

UPLOAD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
)
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_id = process_file(file_path, file.filename)
    if file_id:
        return {"message": "File uploaded and processed", "file_id": file_id}
    else:
        return {"error": "Failed to process file"}


@router.get("/search")
def search(query: str, top_k: int = 5):
    results = search_files(query, top_k)
    return {"results": results}


@router.get("/files")
def list_files():
    files = get_all_files()
    return {"files": files}


@router.get("/files/{file_id}/summary")
def get_file_summary(file_id: int, mode: str = "medium"):
    """
    Get a dynamic summary for a file with a given mode:
    - short  -> 1 sentence
    - medium -> 2 sentences
    - long   -> 4 sentences
    """
    mode = mode.lower()
    if mode not in ("short", "medium", "long"):
        raise HTTPException(status_code=400, detail="Invalid mode. Use short|medium|long")
    summary = summarize_file_by_mode(file_id, mode)
    return {"file_id": file_id, "mode": mode, "summary": summary}


@router.get("/files/{file_id}/similar")
def similar_files(file_id: int, top_k: int = 5):
    """
    Return the most similar other documents to this file.
    """
    similar = find_similar_files(file_id, top_k=top_k)
    return {"file_id": file_id, "similar": similar}


@router.get("/files/{file_id}/duplicates")
def duplicate_files(file_id: int, threshold: float = 0.9):
    """
    Return potential duplicates of this file.
    threshold is a similarity cutoff (0.0 - 1.0). Higher means stricter.
    """
    dups = check_duplicates(file_id, threshold=threshold)
    return {"file_id": file_id, "threshold": threshold, "duplicates": dups}

@router.delete("/files/{file_id}")
def delete_file_route(file_id: int):
    """
    Delete a file from DB + Qdrant.
    """
    result = delete_file(file_id)
    return {"message": "File deleted", "file": result}


@router.post("/reindex")
def reindex_route():
    """
    Rebuild Qdrant index from all files in the SQLite DB.
    """
    result = reindex_all_files()
    return result
