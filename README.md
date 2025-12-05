🌟 AI File Management System
An AI‑powered document management platform with OCR, semantic search, summarization, tags & more.
<p align="center"> <img src="https://img.shields.io/badge/Python-3.10+-blue.svg"> <img src="https://img.shields.io/badge/FastAPI-Enabled-brightgreen"> <img src="https://img.shields.io/badge/Streamlit-Frontend-red"> <img src="https://img.shields.io/badge/Qdrant-Vector%20DB-purple"> <img src="https://img.shields.io/badge/AI-Summarization-yellow"> </p>
🚀 Overview
This system intelligently processes documents by:

Extracting text (PDF/DOCX/Images via OCR)

Generating AI summaries (short/medium/long)

Creating embeddings for semantic search

Finding similar and duplicate files

Auto‑tagging files

Word‑frequency deep search

Displaying everything through a Streamlit UI

Upload → Process → Search → Explore → Compare.

🧩 Phase‑by‑Phase Development
🌱 Base Version (Phase 0)
✔ Upload PDF, DOCX, images
✔ OCR text extraction
✔ Store text + metadata in SQLite
✔ Basic AI summary
✔ List all uploaded files

🔹 Phase 1 — Semantic Embeddings + Qdrant Integration
Added Sentence‑Transformers embeddings

Configured Qdrant vector DB

Added chunking for long documents

Semantic search now returns:

Best‑matching snippet

Summary

Similarity score

Endpoint:

GET /api/search?query=text
🔹 Phase 2 — Dynamic Summaries
Added summary modes:

short → 1 sentence

medium → 2 sentences

long → 4 sentences

Integrated Pegasus‑XSUM for high‑quality summarization

UI button in Streamlit to generate summaries instantly

Endpoint:

GET /api/files/{id}/summary?mode=short|medium|long
🔹 Phase 3 — Similarity & Duplicate Detection
Find similar documents using embeddings

Detect near‑duplicate files using cosine similarity

Streamlit buttons:

Show similar files

Show duplicates

Endpoints:

GET /api/files/{id}/similar
GET /api/files/{id}/duplicates
🔹 Phase 4 — Auto Tagging
Automatic keyword extraction

Tags stored in DB

Added tag-based filtering

Endpoint:

GET /api/files/by-tag?tag=value
🔹 Phase 5 — Word Count Search (Keyword Frequency Engine)
Finds the single file where a word appears most often, across the entire database.

✔ Works with:
PDFs • DOCX • Scanned PDF • Images (OCR-based)

Displays full file content, not just snippets.

Endpoint:

GET /api/search-word?query=word
🖥️ System Architecture
                    +-------------------+
                    |     Streamlit     |
                    |   Frontend (UI)   |
                    +---------+---------+
                              |
                       REST API Calls
                              |
                    +---------v---------+
                    |    FastAPI API    |
                    |  Upload + AI Ops  |
                    | Search + Summary  |
                    +----+---------+----+
                         |         |
             +-----------+         +--------------+
             |                                      |
+------------------------+             +------------------------+
|      SQLite DB        |             |     Qdrant Vector DB   |
|  Text + Metadata      |             |   Embeddings Storage   |
+------------------------+             +------------------------+
                 Structured Data         Semantic Search
⚙️ Setup Instructions
1️⃣ Install dependencies
pip install -r requirements.txt
2️⃣ Initialize the database
python database/init_db.py
3️⃣ Start Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant
4️⃣ Run FastAPI Backend
uvicorn backend.main:app --reload
5️⃣ Start Streamlit Frontend
streamlit run frontend/app.py
🔌 API Quick Reference
📤 Upload File
POST /api/upload
🔍 Semantic Search
GET /api/search?query=text
🔠 Word Count Search
GET /api/search-word?query=word
📝 Summary Modes
GET /api/files/{id}/summary?mode=short|medium|long
🧩 Similar Files
GET /api/files/{id}/similar
🔁 Duplicate Detection
GET /api/files/{id}/duplicates
🏷 Tag Search
GET /api/files/by-tag?tag=keyword
🧑‍💻 Tech Stack
Layer	Technology
Backend	FastAPI
Frontend	Streamlit
Text Storage	SQLite
Semantic Search	Qdrant Vector DB
Embeddings	Sentence‑Transformers
Summarization	Pegasus‑XSUM
OCR	Tesseract
Language	Python
👥 Team Members
Name	Role
Aaron	Backend Engineer
Aleesha	Frontend UI
Anushma	Testing + Documentation
Ben	Backend + AI Pipeline
Christin	Embeddings + Qdrant
🎯 Final Result
A complete, production‑style AI‑powered document intelligence system that can:

✔ Read & parse PDFs, DOCXs, scanned images
✔ Extract text via OCR
✔ Summarize documents (short/medium/long)
✔ Perform semantic search
✔ Find similar & duplicate documents
✔ Auto‑tag and classify files
✔ Rank files by keyword frequency
✔ Provide a full Streamlit UI for interacting