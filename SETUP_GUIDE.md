# 🚀 Setup Guide: AI File Management System

This guide outlines the complete steps to install and set up the AI File Management System from a fresh Git clone on both **Linux** and **Windows** operating systems.

---

## 📋 Prerequisites (Both OS)

Before beginning, ensure your system has the following installed:
1. **[Git](https://git-scm.com/downloads)**: To clone the repository.
2. **[Python 3.10+](https://www.python.org/downloads/)**: The core programming language.
3. **[Docker Desktop / Docker Engine](https://www.docker.com/products/docker-desktop/)**: Required to run the local Qdrant Vector Database.
4. **Tesseract OCR**: Required by the backend to extract text from images and scanned PDFs. *(Installation steps specific to your OS are provided below).*

---

## 🐧 Linux / macOS Setup

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd ai-file-management-system
```

### 2. Install Tesseract OCR
For Debian/Ubuntu-based distributions:
```bash
sudo apt update
sudo apt install -y tesseract-ocr
```
*(For macOS, run: `brew install tesseract`)*

### 3. Create & Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
*(Note: If you run into memory errors during `pip install`, use `pip install --no-cache-dir -r requirements.txt`)*

### 5. Start the Qdrant Vector Database
Make sure Docker is running on your machine, then launch Qdrant in the background:
```bash
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant
```

### 6. Initialize the Application Database
```bash
python database/init_db.py
```

### 7. Run the Application
You will need **two terminal windows** (ensure the virtual environment is activated in both using `source venv/bin/activate`).

**Terminal 1 (Backend):**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
streamlit run frontend/app.py
```
The application will automatically open in your default web browser at `http://localhost:8501`.

---
---

## 🪟 Windows Setup

### 1. Clone the Repository
Open Command Prompt (CMD) or PowerShell:
```cmd
git clone <your-repository-url>
cd ai-file-management-system
```

### 2. Install Tesseract OCR
1. Download the latest Windows installer for Tesseract from [UB-Mannheim's GitHub](https://github.com/UB-Mannheim/tesseract/wiki).
2. Run the installer (it usually installs to `C:\Program Files\Tesseract-OCR`).
3. **Crucial:** Add `C:\Program Files\Tesseract-OCR` to your Windows System Environment Variables `Path`.

### 3. Create & Activate a Virtual Environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### 4. Install Python Dependencies
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Start the Qdrant Vector Database
Open the **Docker Desktop** application and wait for the Docker engine to turn green (Running). Then, in your terminal, run:
```cmd
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant
```

### 6. Initialize the Application Database
```cmd
python database\init_db.py
```

### 7. Run the Application
You will need **two terminal windows** (ensure the virtual environment is activated in both using `venv\Scripts\activate`).

**Terminal 1 (Backend):**
```cmd
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```cmd
streamlit run frontend/app.py
```
The application will automatically open in your default web browser at `http://localhost:8501`.

---

## 🛠️ Troubleshooting

- **`ModuleNotFoundError: No module named 'torch'`** -> Your pip cache might have run out of disk space during installation. Try running `pip cache purge` and then reinstall using `pip install --no-cache-dir torch==2.5.1 sentence-transformers==3.2.1`.
- **`sqlite3.OperationalError`** -> You forgot to run `python database/init_db.py` to build the required tables.
- **Tesseract Not Found (Windows)** -> You need to close and reopen your terminals after adding Tesseract to your PATH variable.
