🌟 AI File Management System
An AI‑powered document intelligence platform that enables intelligent document processing, semantic search, summarization, tagging, duplicate detection, merging, and AI‑assisted document rewriting through an interactive Streamlit interface.

🚀 Overview
The AI File Management System is designed to help users upload, analyze, search, compare, merge, and transform documents intelligently using modern AI techniques.

Core Capabilities
📄 Upload documents (PDF, DOCX, images)

🔍 Extract text using OCR

✨ Generate AI summaries (short / medium / long)

🧠 Perform semantic search using embeddings

🔗 Find similar and duplicate documents

🏷 Automatically tag documents

🔡 Perform keyword frequency (word count) search

🧩 Merge multiple files into a single document

🤖 AI chatbot for document rewriting, shortening, and topic‑focused extraction

⬇ Download outputs as TXT, DOCX, or PDF

🖥 Full-featured Streamlit UI

Workflow:
Upload → Process → Search → Explore → Compare → Merge → Rewrite → Download

🧩 Phase‑by‑Phase Development
🌱 Phase 0 — Base Version (Foundation)
✔ File upload (PDF, DOCX, Images)
✔ OCR text extraction using Tesseract
✔ Store extracted text & metadata in SQLite
✔ Basic AI summarization
✔ List and view uploaded files

🔹 Phase 1 — Semantic Embeddings & Vector Search
✔ Sentence‑Transformers embeddings
✔ Integrated Qdrant Vector Database
✔ Chunk‑based embeddings for large documents
✔ Semantic search returns:

Best matching snippet

Document summary

Similarity score

Endpoint

GET /api/search?query=text
🔹 Phase 2 — Dynamic AI Summaries
✔ Summary modes:

Mode	Description	Output
short	Ultra‑brief	1 sentence
medium	Balanced	2 sentences
long	Detailed	4 sentences
✔ Powered by Pegasus‑XSUM
✔ UI control added in Streamlit

Endpoint

GET /api/files/{id}/summary?mode=short|medium|long
🔹 Phase 3 — Similarity & Duplicate Detection
✔ Embedding‑based similarity detection
✔ High‑threshold duplicate detection
✔ Streamlit actions:

Show similar files

Show duplicate files

Endpoints

GET /api/files/{id}/similar
GET /api/files/{id}/duplicates
🔹 Phase 4 — Auto‑Tagging System
✔ Keyword extraction from summaries
✔ Tags stored in database
✔ Filter files using tags

Endpoint

GET /api/files/by-tag?tag=value
🔹 Phase 5 — Word Count Search (Keyword Frequency Engine)
✔ Finds the file where a keyword appears most frequently
✔ Works with:

PDFs

DOCX

Scanned PDFs

Images (OCR)
✔ Displays full content with highlights

Endpoint

GET /api/search-word?query=word
🔹 Phase 6 — File Merge & Export System
✔ Select multiple files from database
✔ Merge content in selected order
✔ Save merged file to database
✔ Download merged file as:

.txt

.docx

.pdf

Endpoint

POST /api/files/merge
🔹 Phase 7 — AI Document Chatbot (Groq‑Powered)
✔ Upload document from:

Database

Local system
✔ Ask AI to:

Shorten documents (e.g., 500 or 1000 words)

Focus on a specific topic

Rewrite content cleanly
✔ Powered by Groq (LLaMA‑3.3‑70B‑Versatile)
✔ Download AI‑generated output as TXT / DOCX / PDF

Endpoints

POST /api/chat
POST /api/chat/convert
🖥 System Architecture
+-----------------------+
|   Streamlit Frontend  |
+----------+------------+
           |
           | REST API
           v
+-----------------------------+
|     FastAPI Backend         |
| - OCR & Processing          |
| - Summarization             |
| - Semantic Search           |
| - File Merge & Chatbot      |
+-----------+-----------------+
            |
     +------+------+
     |             |
     v             v
+-----------+  +------------------+
| SQLite DB |  | Qdrant Vector DB |
| Metadata  |  | Embeddings Store |
+-----------+  +------------------+
⚙️ Setup Instructions
1️⃣ Install Dependencies
pip install -r requirements.txt
2️⃣ Initialize Database
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
📝 Summary
GET /api/files/{id}/summary?mode=short|medium|long
🧩 Similar Files
GET /api/files/{id}/similar
🔁 Duplicate Detection
GET /api/files/{id}/duplicates
🏷 Tag Search
GET /api/files/by-tag?tag=keyword
🧩 Merge Files
POST /api/files/merge
🤖 AI Chatbot
POST /api/chat
POST /api/chat/convert
🧑‍💻 Tech Stack
Layer	Technology
Backend	FastAPI
Frontend	Streamlit
Database	SQLite
Vector DB	Qdrant
Embeddings	Sentence‑Transformers
Summarization	Pegasus‑XSUM
AI Chat	Groq (LLaMA‑3.3‑70B)
OCR	Tesseract
Language	Python
👥 Team Members
Aaron Tom

Aleesha Maria

Anushma Prasad

Ben Sebastian Joseph

Christin Toms

🎯 Final Outcome
A production‑style AI document intelligence system capable of:

✔ Reading PDFs, DOCX files, and images
✔ OCR‑based text extraction
✔ AI summarization (short / medium / long)
✔ Semantic search with embeddings
✔ Similarity & duplicate detection
✔ Auto‑tagging
✔ Keyword‑frequency analysis
✔ File merging & multi‑format export
✔ AI‑powered document rewriting
✔ Full Streamlit user interface