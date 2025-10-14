# extract.py
import fitz  # PyMuPDF

def extract_text_from_pdf(path: str) -> str:
    doc = fitz.open(path)
    texts = []
    for page in doc:
        texts.append(page.get_text())   # page.get_text() returns text for that page
    doc.close()
    return "\n".join(texts)
