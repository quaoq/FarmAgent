from pypdf import PdfReader

def extract_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text())
    return "\n\n".join(text)
