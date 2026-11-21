import os
import sys
import secrets
import warnings
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

INSECURE_JWT_SECRETS = {
    "change-me-in-production-use-a-real-secret-key-at-least-32-chars",
    "brand_sentinel_secure_jwt_secret_2026_key",
    "secret",
    "changeme",
    "test_secret",
}


class Settings(BaseSettings):
    # Core settings
    database_url: str = "sqlite:///./brandsentinel.db"
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120
    environment: str = "development"

    # CORS settings
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

    @model_validator(mode="after")
    def validate_jwt_secret_security(self):
        env = (self.environment or "development").strip().lower()
        secret = self.jwt_secret_key

        if env == "production":
            if not secret or secret in INSECURE_JWT_SECRETS or len(secret) < 32:
                raise RuntimeError(
                    "FATAL SECURITY VIOLATION: JWT_SECRET_KEY is missing, insecure, or shorter than 32 characters "
                    "in production environment. You must set a cryptographically strong secret in the environment."
                )
        else:
            # Dev or test mode: if secret is not set or empty, generate an ephemeral cryptographically strong secret
            if not secret:
                self.jwt_secret_key = secrets.token_hex(32)
                warnings.warn(
                    "SECURITY NOTICE: JWT_SECRET_KEY was not configured in environment. "
                    "Generated an ephemeral 256-bit secret for non-production session.",
                    UserWarning,
                )
        return self


settings = Settings()
