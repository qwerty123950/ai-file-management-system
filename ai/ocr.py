import pytesseract
from pytesseract import TesseractNotFoundError
from PIL import Image
import pdfplumber
from docx import Document
import os

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    try:
        # --- PDFs ---
        if ext == ".pdf":
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text += page_text + "\n\n"
                    else:
                        pil_img = page.to_image(resolution=300).original
                        ocr_text = pytesseract.image_to_string(pil_img) or ""
                        text += ocr_text + "\n\n"
            return text.strip()

        # --- Image files ---
        elif ext in [".png", ".jpg", ".jpeg"]:
            image = Image.open(file_path)
            return pytesseract.image_to_string(image)

        # --- Word docs ---
        elif ext == ".docx":
            doc = Document(file_path)
            return "\n".join(para.text for para in doc.paragraphs)

        else:
            return "Unsupported file type"

    except TesseractNotFoundError:
        # 🔹 graceful degradation
        return "OCR engine not available on this system"
