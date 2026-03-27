import os
from pydantic import BaseModel


class Settings(BaseModel):
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    collection_name: str = os.getenv("COLLECTION_NAME", "research_chunks")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    chat_model: str = os.getenv("CHAT_MODEL", "llama3.2")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "900"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")


settings = Settings()