import pytesseract
from PIL import Image
import pdfplumber
from docx import Document
import os

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        with pdfplumber.open(file_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() or ''
        return text
    elif ext in ['.png', '.jpg', '.jpeg']:
        image = Image.open(file_path)
        return pytesseract.image_to_string(image)
    elif ext == '.docx':
        doc = Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    else:
        return "Unsupported file type"