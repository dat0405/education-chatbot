from dotenv import load_dotenv
load_dotenv()

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    admin_upload_key: str = ""
    openai_vector_store_id: str = ""
    upload_dir: str = "uploads"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()