"""Test configuration – uses in-process SQLite regardless of .env DATABASE_URL."""
import os

# Override BEFORE any app import touches settings / session
os.environ["DATABASE_URL"] = "sqlite:///./test_brandsentinel.db"
os.environ["SEED_DEMO"] = "false"
os.environ["ENVIRONMENT"] = "testing"
os.environ["GEMINI_API_KEY"] = ""
os.environ["LLM_MODEL"] = "mock"

import pytest
from backend.app.db import session, models


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once per test session and configure test settings."""
    import pathlib
    db_path = pathlib.Path("test_brandsentinel.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass
    from backend.app.core.config import settings
    settings.gemini_api_key = ""
    settings.llm_model = "mock"
    settings.environment = "testing"
    models.Base.metadata.create_all(bind=session.engine)
    from backend.app.main import ensure_schema_columns
    ensure_schema_columns(session.engine)
    yield
    # Clean up test database file
    import pathlib
    db_path = pathlib.Path("test_brandsentinel.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass
