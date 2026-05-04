import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi import Header

from app.config import settings
from app.schemas import (
    ChatRequest,
    ChatResponse,
    UploadResponse,
    UploadItem,
    DocumentItem,
    DeleteResponse
)
from app.database import SessionLocal, init_db, Document
from app.ingest import ingest_file
from app.rag import generate_answer, ensure_vector_store, delete_document_chunks

app = FastAPI(title="Education Expert RAG API")

os.makedirs(settings.upload_dir, exist_ok=True)
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Education Expert RAG API is running"}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("app/favicon.ico")


@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    x_admin_key: str | None = Header(None)
):
    if x_admin_key != settings.admin_upload_key:
        raise HTTPException(status_code=403, detail="Not allowed")
        

    if file is None:
        raise HTTPException(status_code=400, detail="No file uploaded")

    save_path = os.path.join(settings.upload_dir, file.filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        doc = ingest_file(db=db, file_path=save_path, filename=file.filename)

        uploaded_item = UploadItem(
            document_id=doc.id,
            filename=doc.filename,
            chunks_indexed=doc.chunk_count,
            status=doc.status
        )

        return UploadResponse(uploaded=[uploaded_item])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(save_path):
            os.remove(save_path)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    user_message = req.messages[-1].content.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Empty user message")

    vector_store_id = ensure_vector_store()
    answer = generate_answer(user_message, vector_store_id)

    return ChatResponse(
        answer=answer,
        sources=[]
    )


@app.get("/documents", response_model=list[DocumentItem])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        DocumentItem(
            document_id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            status=doc.status,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at.isoformat()
        )
        for doc in docs
    ]


@app.delete("/documents/{document_id}", response_model=DeleteResponse)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_chunks(document_id)
    db.delete(doc)
    db.commit()

    return DeleteResponse(
        success=True,
        document_id=document_id,
        deleted=True
    )