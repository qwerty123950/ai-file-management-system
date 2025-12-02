# ai/preprocess.py

import re


def clean_text(text: str) -> str:
    """
    Basic cleanup for OCR / extracted text:
    - normalize whitespace
    - collapse crazy newlines
    - remove empty lines
    """
    if not text:
        return ""

    # Normalize CRLF and multiple spaces
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove empty lines
    lines = [ln.rstrip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln.strip() != ""]

    cleaned = "\n".join(lines).strip()
    return cleaned
