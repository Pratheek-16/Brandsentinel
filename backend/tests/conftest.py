import pytest
from backend.app.db import session, models

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    models.Base.metadata.create_all(bind=session.engine)
    yield
