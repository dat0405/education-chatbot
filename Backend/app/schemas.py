from pydantic import BaseModel
from typing import List, Optional, Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class SourceItem(BaseModel):
    document_id: str
    source: str
    chunk_id: str
    text_preview: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]


class UploadItem(BaseModel):
    document_id: str
    filename: str
    chunks_indexed: int
    status: str


class UploadResponse(BaseModel):
    success: bool
    uploaded: List[UploadItem]


class DocumentItem(BaseModel):
    document_id: str
    filename: str
    file_type: str
    status: str
    chunk_count: int
    created_at: str


class DeleteResponse(BaseModel):
    success: bool
    document_id: str
    deleted: bool


class ErrorResponse(BaseModel):
    error: str