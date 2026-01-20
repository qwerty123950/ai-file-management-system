#backend/routes/chat.py

from fastapi import  APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.chat_service import groq_chat
from fastapi.responses import StreamingResponse
import io
from backend.services.file_service import (
    to_txt, 
    to_docx, 
    to_pdf,
    )

router = APIRouter()

class ChatRequest(BaseModel):
    content: str
    instruction: str

@router.post("/chat")
def chat(req: ChatRequest):
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Empty content")
    
    if not req.instruction.strip():
        raise HTTPException(status_code=400, detail="Empty instruction")

    try:
        result = groq_chat(
            document=req.content,
            instruction=req.instruction,
        )
        return {"result": result}
    except Exception as e:
        print("❌ Groq error:", e)  # IMPORTANT for debugging
        raise HTTPException(status_code=500, detail="Groq processing failed")

@router.post("/chat/convert")
def convert_chat_result(req: dict):
    text = req.get("content", "")
    fmt = req.get("format")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty content")

    if fmt == ".txt":
        return StreamingResponse(
            io.BytesIO(to_txt(text)),
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=chat_result.txt"},
        )

    elif fmt == ".docx":
        return StreamingResponse(
            io.BytesIO(to_docx(text)),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=chat_result.docx"},
        )

    elif fmt == ".pdf":
        return StreamingResponse(
            io.BytesIO(to_pdf(text)),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=chat_result.pdf"},
        )

    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
