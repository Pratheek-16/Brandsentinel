"""Test configuration – uses in-process SQLite regardless of .env DATABASE_URL."""
import os

# Override BEFORE any app import touches settings / session
os.environ["DATABASE_URL"] = "sqlite:///./test_brandsentinel.db"
os.environ["SEED_DEMO"] = "false"
os.environ["ENVIRONMENT"] = "testing"

import pytest
from backend.app.db import session, models


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once per test session."""
    models.Base.metadata.create_all(bind=session.engine)
    yield
    # Clean up test database file
    import pathlib
    db_path = pathlib.Path("test_brandsentinel.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass
