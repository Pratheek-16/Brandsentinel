import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Core settings — let pydantic-settings resolve from env vars / .env file
    database_url: str = "sqlite:///./brandsentinel.db"
    jwt_secret_key: str = "brand_sentinel_secure_jwt_secret_2026_key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120
    environment: str = "development"

    # CORS settings (explicit development and production origins, no wildcard)
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )

    @property
    def allowed_cors_origins(self) -> List[str]:
        origins = self.cors_origins.split(",")
        origins.append("https://brandsentinel-f5j8.onrender.com")
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if render_url:
            origins.append(render_url)
        return list(dict.fromkeys(origin.strip() for origin in origins if origin.strip()))

    # Uploads settings
    upload_dir: str = "uploads"
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB limit
    allowed_upload_extensions: List[str] = [".txt", ".md", ".docx", ".pdf", ".png", ".jpg", ".jpeg"]

    # LLM provider settings
    gemini_api_key: str = ""
    gemini_project_id: str = ""
    llm_model: str = "mock"

    # Feature flags
    seed_demo: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
