import os
from uuid import uuid4
from sqlalchemy.orm import Session
from app.config import settings
from app.database import Document
from app.utils import extract_text, chunk_text
from app.rag import upsert_chunks


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def ingest_file(db: Session, file_path: str, filename: str):
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    document_id = str(uuid4())

    doc = Document(
        id=document_id,
        filename=filename,
        file_type=ext,
        status="processing",
        chunk_count=0
    )
    db.add(doc)
    db.commit()

    text = extract_text(file_path)
    chunks = chunk_text(
        text=text,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap
    )

    chunk_count = upsert_chunks(
        document_id=document_id,
        source_name=filename,
        chunks=chunks
    )

    doc.status = "indexed"
    doc.chunk_count = chunk_count
    db.commit()
    db.refresh(doc)

    return doc