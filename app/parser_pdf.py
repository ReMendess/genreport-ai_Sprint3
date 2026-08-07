import fitz


def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    try:
        pages = [page.get_text() for page in doc]
        return "\n".join(text for text in pages if text)
    finally:
        doc.close()
