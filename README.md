🌟 AI File Management System

An AI‑powered document intelligence platform that enables intelligent document processing, semantic search, summarization, tagging, duplicate detection, merging, and AI‑assisted document rewriting through an interactive Streamlit interface.

🚀 Overview

The AI File Management System is designed to help users upload, analyze, search, compare, merge, and transform documents intelligently using modern AI techniques.

Core Capabilities

📄 Upload documents (PDF, DOCX, images)

🔍 Extracting text via OCR

✨ Generating AI summaries (short / medium / long)

🧠 Creating embeddings for semantic search

🔗 Finding similar and duplicate files

🏷 Auto‑tagging files

🔡 Keyword‑frequency deep search

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

	✔ Store text + metadata in SQLite

	✔ Basic AI summary

	✔ List all uploaded files


🔹 Phase 1 — Semantic Embeddings + Qdrant


	✔ Added Sentence‑Transformers embeddings

	✔ Integrated Qdrant vector database

	✔ Added chunk‑based embedding for long documents

	✔ Semantic search now returns:

		✔ Best‑matching snippet
	
		✔ Document summary
	
		✔ Similarity score


✔ Endpoint:   

	GET /api/search?query=text
	
🔹 Phase 2 — Dynamic Summaries

	✔ Summary modes added:

	Mode	Meaning	    Sentences
	
	short	ultra‑brief	1 sentence
	medium	balanced	2 sentences
	long	detailed	4 sentences

	✔ Powered by Pegasus‑XSUM summarization model.

	✔ UI control added in Streamlit

✔ Endpoint:  
	
	GET /api/files/{id}/summary?mode=short|medium|long

🔹 Phase 3 — Similarity & Duplicate Detection

	✔ Embedding‑based similar document search

	✔ High‑similarity duplicate detection

	✔ Streamlit buttons:

		✔ Show similar files
	
		✔ Show duplicates
	

✔ Endpoints:

    GET /api/files/{id}/similar
	
    GET /api/files/{id}/duplicates

🔹 Phase 4 — Auto‑Tagging System

	✔ Extracts keywords from summaries

	✔ Stores tags inside database

	✔ Tag‑based file filter

✔ Endpoint:   

	GET /api/files/by-tag?tag=value

🔹 Phase 5 — Word Count Search (Keyword Frequency Engine)

	Finds the file where a word appears the most times, using full document content.

	✔ Works with: PDF / DOCX / Scanned PDF / Images

	✔ Uses OCR + text search

	✔ Shows full file content


✔ Endpoint:    

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
        |      Streamlit UI     |
        +----------+------------+
                   |
                   | REST API
                   v
        +-----------------------------+
        |        FastAPI Backend      |
        |  - Upload processing        |
        |  - OCR & Preprocessing      |
		|  - Summarization            |
        |  - Semantic Search          |
		|  - File Merge & Chatbox     |
        +-----------+-----------------+
                    |
        +-----------+-------------+
        |                         |
        v                         v
    +-----------+         +------------------+
    | SQLite DB |         | Qdrant Vector DB |
    | Metadata  |         | Embeddings Store |
    +-----------+         +------------------+


⚙️ Setup Instructions

1️⃣ Install dependencies

    pip install -r requirements.txt
2️⃣ Initialize the database

    python database/init_db.py
3️⃣ Start Qdrant (Docker)

    docker run -p 6333:6333 qdrant/qdrant
4️⃣ Run FastAPI backend

    uvicorn backend.main:app --reload
5️⃣ Start Streamlit frontend

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

	Layer	            Technology

	✔ Backend	        FastAPI
	✔ Frontend	        Streamlit
	✔ Text Storage	    SQLite
	✔ Semantic Search	Qdrant Vector DB
	✔ Embeddings	    Sentence‑Transformers
	✔ Summarization	    Pegasus‑XSUM
	✔ OCR	            Tesseract
	✔ Language	        Python

👥 Team Members
	
	Aaron Tom

	Aleesha Maria

	Anushma	Prasad

	Ben	Sebastian Joseph

	Christin Toms	

🎯 Final Result

A production‑style AI document intelligence system capable of:

	✔ Reading PDFs, DOCXs, images

	✔ Extracting text via OCR

	✔ Summarizing (short, medium, long)

	✔ Semantic search

	✔ Finding similar & duplicate docs

	✔ Auto‑tagging

	✔ Keyword‑frequency ranking
	
	✔ Full Streamlit interface
