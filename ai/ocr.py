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
            import gc
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text += page_text + "\n\n"
                        else:
                            # Memory optimized OCR - lowered from 200 to 150 DPI due to OOM crashes
                            img_obj = page.to_image(resolution=150)
                            pil_img = img_obj.original.convert('L') # Convert to grayscale
                            ocr_text = pytesseract.image_to_string(pil_img) or ""
                            text += ocr_text + "\n\n"
                            
                            # Explicit cleanup
                            del pil_img
                            del img_obj
                            gc.collect()
                    except Exception as e:
                        print(f"Failed to extract page from {file_path}: {e}")
                        continue
            
            return text.strip()

        # --- Image files ---
        elif ext in [".png", ".jpg", ".jpeg"]:
            from pytesseract import Output
            image = Image.open(file_path).convert('L') # Grayscale for better accuracy
            
            # Extract word bounding boxes using PSM 11
            data = pytesseract.image_to_data(image, config='--psm 11', output_type=Output.DICT)
            
            words = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                if not text or conf < 10:
                    continue
                words.append({
                    'text': text,
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'right': data['left'][i] + data['width'][i],
                    'bottom': data['top'][i] + data['height'][i],
                    'cx': data['left'][i] + data['width'][i] / 2,
                    'cy': data['top'][i] + data['height'][i] / 2
                })
                
            # Cluster words if they are close together
            blocks = []
            X_GAP_THRESH = 80
            Y_GAP_THRESH = 40
            
            def boxes_intersect_or_close(w1, w2):
                h_gap = max(0, max(w1['left'], w2['left']) - min(w1['right'], w2['right']))
                v_gap = max(0, max(w1['top'], w2['top']) - min(w1['bottom'], w2['bottom']))
                return h_gap <= X_GAP_THRESH and v_gap <= Y_GAP_THRESH

            for word in words:
                matched_blocks = []
                for i, block in enumerate(blocks):
                    if any(boxes_intersect_or_close(word, bw) for bw in block):
                        matched_blocks.append(i)
                
                if not matched_blocks:
                    blocks.append([word])
                else:
                    first_idx = matched_blocks[0]
                    blocks[first_idx].append(word)
                    for other_idx in sorted(matched_blocks[1:], reverse=True):
                        blocks[first_idx].extend(blocks[other_idx])
                        blocks.pop(other_idx)

            # Format the clustered blocks
            formatted_blocks = []
            for block in blocks:
                # Group words into physical lines within the block
                block.sort(key=lambda w: (w['cy'] // 15, w['cx']))
                lines = []
                curr_line = []
                curr_y = None
                
                for w in block:
                    if curr_y is None:
                        curr_y = w['cy']
                        curr_line.append(w)
                    elif abs(w['cy'] - curr_y) <= 15:
                        curr_line.append(w)
                    else:
                        lines.append(curr_line)
                        curr_line = [w]
                        curr_y = w['cy']
                if curr_line: lines.append(curr_line)
                
                block_text = "\n".join([" ".join([w['text'] for w in line]) for line in lines])
                formatted_blocks.append({
                    'text': block_text, 'x': min(w['left'] for w in block), 'y': min(w['top'] for w in block)
                })
                
            # Sort final blocks top-to-bottom, left-to-right based on general Y bands
            formatted_blocks.sort(key=lambda b: (b['y'] // 80, b['x']))
            
            return "\n\n".join([f"- {b['text']}" for b in formatted_blocks])

        # --- Word docs ---
        elif ext == ".docx":
            doc = Document(file_path)
            return "\n".join(para.text for para in doc.paragraphs)

        else:
            return "Unsupported file type"

    except TesseractNotFoundError:
        # 🔹 graceful degradation
        return "OCR engine not available on this system"
