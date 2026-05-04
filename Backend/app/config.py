from dotenv import load_dotenv
load_dotenv()

import os
from pydantic import BaseModel


class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_vector_store_id: str = os.getenv("OPENAI_VECTOR_STORE_ID", "")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "900"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    admin_upload_key: str
    

settings = Settings()