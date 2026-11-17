import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    # Core settings
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./brandsentinel.db")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "replace_me_with_a_secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # LLM provider settings
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_project_id: str = os.getenv("GEMINI_PROJECT_ID", "")
    llm_model: str = os.getenv("LLM_MODEL", "mock")

    # Feature flags
    seed_demo: bool = os.getenv("SEED_DEMO", "false").lower() == "true"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
