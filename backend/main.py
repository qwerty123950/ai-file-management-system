from fastapi import FastAPI
from backend.routes.files import router as files_router

app = FastAPI()

app.include_router(files_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Hello, AI-Driven File Management System is running 🚀"}