from fastapi import APIRouter, UploadFile, File
import shutil
import os

from backend.services.file_service import (
    process_file,
    search_files,
    get_all_files,
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
