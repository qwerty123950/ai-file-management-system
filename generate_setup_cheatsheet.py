from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", "B", 14)
pdf.cell(200, 10, "AI-Driven File Management System", ln=True, align="C")
pdf.cell(200, 10, "Setup Cheat Sheet (Python 3.13 Edition)", ln=True, align="C")
pdf.ln(10)

pdf.set_font("Courier", size=10)

content = """
STEP 1. Clone the Repository
    git clone https://github.com/<your-team-repo>.git
    cd ai-file-management-system

STEP 2. Create and Activate Virtual Environment
    python -m venv venv
    venv\\Scripts\\activate   # Windows
    source venv/bin/activate # Mac/Linux

STEP 3. Upgrade pip
    python -m pip install --upgrade pip setuptools wheel

STEP 4. Install Dependencies
    pip install -r requirements.txt

    (requirements.txt must contain:)
    fastapi==0.115.0
    uvicorn==0.30.6
    streamlit==1.39.0
    psycopg2-binary==2.9.10
    SQLAlchemy==2.0.36
    qdrant-client==1.13.2
    sentence-transformers==3.2.1
    transformers==4.46.3
    torch==2.7.0
    pytesseract==0.3.13
    python-docx==1.1.2
    PyPDF2==3.0.1
    pdfplumber==0.11.0

STEP 5. Set Up PostgreSQL Database
    CREATE DATABASE file_manager;

STEP 6. Run Qdrant Vector DB
    docker run -p 6333:6333 qdrant/qdrant
    -> Test in browser: http://localhost:6333/dashboard

STEP 7. Install and Verify Tesseract OCR
    tesseract --version

STEP 8. Run FastAPI Backend
    uvicorn backend.main:app --reload
    -> Visit: http://127.0.0.1:8000/docs

STEP 9. Run Streamlit Frontend
    streamlit hello

STEP 10. Verify Installation
    python -c "import torch, transformers, fastapi, streamlit; \
print('Torch:', torch.__version__, '| Transformers:', transformers.__version__)"
    Expected: Torch 2.7.0 | Transformers 4.46.3
"""

pdf.multi_cell(0, 7, content)

pdf.output("setup_cheatsheet.pdf")
print("✅ Step-by-step cheat sheet created: setup_cheatsheet.pdf")