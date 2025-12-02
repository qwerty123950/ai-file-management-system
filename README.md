# AI File Management System

An AI-driven file management system that uses OCR, embeddings, summarization, and deduplication to manage and search files.

## Features
- Upload files (PDF, DOCX, images)
- Extract text using OCR
- Generate summaries
- Semantic search using embeddings
- Deduplication detection

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Initialize database: `python database/init_db.py`
3. Start Qdrant: Use docker-compose or local instance
4. Run backend: `uvicorn backend.main:app --reload`
5. Run frontend: `streamlit run frontend/app.py`

## Team Members
- Aaron
- Aleesha
- Anushma
- Ben
- Christin
