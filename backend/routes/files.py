# backend/routes/files.py

from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import zipfile
import io

from backend.services.file_service import (
    process_file,
    search_files,
    get_all_files,
    summarize_file_by_mode,
    find_similar_files,
    check_duplicates,
    delete_file,
    reindex_all_files,
    get_files_by_tag,
    search_file_by_word,
    search_file_by_word_count,
)

router = APIRouter()

UPLOAD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ===============================
# Upload: FILES + ZIP
# ===============================
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename")

    filename = file.filename.lower()

    # ZIP handling
    if filename.endswith(".zip"):
        zip_bytes = await file.read()

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith("/"):
                    continue

                safe_path = os.path.normpath(member)
                if safe_path.startswith(".."):
                    continue

                full_path = os.path.join(UPLOAD_DIR, safe_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                with zip_ref.open(member) as src, open(full_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                process_file(full_path, os.path.basename(member))

        return {"message": "ZIP uploaded and extracted successfully"}

    # Normal file
    safe_name = os.path.basename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_id = process_file(file_path, safe_name)
    return {"message": "File uploaded", "file_id": file_id}

# ===============================
# List all files
# ===============================
@router.get("/files")
def list_files():
    return get_all_files()


# ===============================
# Semantic search
# ===============================
@router.get("/search")
def semantic_search(query: str):
    return search_files(query)


# ===============================
# Word-based search
# ===============================
@router.get("/search/word")
def word_search(word: str):
    return search_file_by_word(word)


# ===============================
# Dynamic summary (short / medium / long)
# ===============================
@router.get("/files/{file_id}/summary")
def get_summary(file_id: int, mode: str = "medium"):
    return {
        "file_id": file_id,
        "mode": mode,
        "summary": summarize_file_by_mode(file_id, mode),
    }


# ===============================
# Similar files
# ===============================
@router.get("/files/{file_id}/similar")
def similar_files(file_id: int, top_k: int = 5):
    return find_similar_files(file_id, top_k)


# ===============================
# Duplicate detection
# ===============================
@router.get("/files/{file_id}/duplicates")
def duplicate_files(file_id: int, threshold: float = 0.9):
    return check_duplicates(file_id, threshold)


# ===============================
# Delete file
# ===============================
@router.delete("/files/{file_id}")
def remove_file(file_id: int):
    return delete_file(file_id)


# ===============================
# Reindex all files
# ===============================
@router.post("/reindex")
def reindex():
    return reindex_all_files()


# ===============================
# Filter by tag
# ===============================
@router.get("/files/tag/{tag}")
def files_by_tag(tag: str):
    return get_files_by_tag(tag)

# # ===============================
# # LIST FILES
# # ===============================
# @router.get("/files")
# def list_files():
#     return get_all_files()


# # ===============================
# # SEMANTIC SEARCH
# # ===============================
# @router.get("/search")
# def semantic_search(query: str, top_k: int = 5):
#     return search_files(query, top_k)


# # ===============================
# # WORD SEARCH
# # ===============================
# @router.get("/search/word")
# def word_search(word: str):
#     result = search_file_by_word(word)
#     if not result:
#         raise HTTPException(status_code=404, detail="No matching file found")
#     return result


# # ===============================
# # FILE SUMMARY MODES
# # ===============================
# @router.get("/summary/{file_id}")
# def get_summary(file_id: int, mode: str = "medium"):
#     return summarize_file_by_mode(file_id, mode)


# # ===============================
# # SIMILAR FILES
# # ===============================
# @router.get("/similar/{file_id}")
# def similar_files(file_id: int):
#     return find_similar_files(file_id)


# # ===============================
# # DUPLICATES
# # ===============================
# @router.get("/duplicates/{file_id}")
# def duplicate_files(file_id: int):
#     return check_duplicates(file_id)


# # ===============================
# # TAG FILTER
# # ===============================
# @router.get("/tags")
# def files_by_tag(tag: str):
#     return get_files_by_tag(tag)


# # ===============================
# # DELETE FILE
# # ===============================
# @router.delete("/files/{file_id}")
# def remove_file(file_id: int):
#     return delete_file(file_id)


# # ===============================
# # REINDEX
# # ===============================
# @router.post("/reindex")
# def reindex():
#     return reindex_all_files()
