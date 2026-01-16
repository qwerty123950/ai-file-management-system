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
# Upload: supports FILES + ZIP FOLDERS
# ===============================
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename")

    filename = file.filename.lower()

    # ---------------- ZIP HANDLING ----------------
    if filename.endswith(".zip"):
        zip_bytes = await file.read()

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith("/"):
                    continue

                safe_path = os.path.normpath(member)

                # Prevent zip-slip
                if safe_path.startswith(".."):
                    continue

                full_path = os.path.join(UPLOAD_DIR, safe_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                with zip_ref.open(member) as src, open(full_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                process_file(full_path, os.path.basename(member))

        return {"message": "ZIP uploaded and extracted successfully"}

    # ---------------- NORMAL FILE ----------------
    safe_name = os.path.basename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_id = process_file(file_path, safe_name)
    return {"message": "File uploaded", "file_id": file_id}
