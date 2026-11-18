import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Core settings
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./brandsentinel.db")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "brand_sentinel_secure_jwt_secret_2026_key")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    environment: str = os.getenv("ENVIRONMENT", "development")

    # CORS settings (explicit development and production origins, no wildcard)
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Uploads settings
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB limit
    allowed_upload_extensions: List[str] = [".txt", ".md", ".docx", ".pdf", ".png", ".jpg", ".jpeg"]

    # LLM provider settings
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_project_id: str = os.getenv("GEMINI_PROJECT_ID", "")
    llm_model: str = os.getenv("LLM_MODEL", "mock")

    # Feature flags
    seed_demo: bool = os.getenv("SEED_DEMO", "false").lower() == "true"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
