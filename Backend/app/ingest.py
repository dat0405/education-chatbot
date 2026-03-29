import os
from uuid import uuid4
from sqlalchemy.orm import Session
from app.database import Document
from app.rag import (
    ensure_vector_store,
    upload_file_to_openai,
    add_file_to_vector_store,
    wait_until_file_ready,
)

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
        chunk_count=1
    )
    db.add(doc)
    db.commit()

    vector_store_id = ensure_vector_store()
    file_id = upload_file_to_openai(file_path)
    vs_file = add_file_to_vector_store(vector_store_id, file_id)
    wait_until_file_ready(vector_store_id, vs_file.id)

    doc.status = "indexed"
    db.commit()
    db.refresh(doc)

    return doc