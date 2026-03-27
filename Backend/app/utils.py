from pypdf import PdfReader
from docx import Document as DocxDocument
import os


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == ".docx":
        doc = DocxDocument(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    raise ValueError(f"Unsupported file type: {ext}")


def clean_text(text: str) -> str:
    return " ".join(text.split())


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    text = clean_text(text)
    chunks = []
    start = 0

    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks