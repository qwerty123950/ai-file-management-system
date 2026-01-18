from fastapi import FastAPI
from backend.routes.files import router as files_router
from backend.services.file_service import init_db, init_qdrant

app = FastAPI()

app.include_router(files_router, prefix="/api")

@app.on_event("startup")
def startup():
    init_db()
    init_qdrant()

@app.get("/")
def root():
    return {"message": "AI-Driven File Management System running 🚀"}
