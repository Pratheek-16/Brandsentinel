import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ai_provider" in data
    assert "name" in data["ai_provider"]
    assert "status" in data["ai_provider"]
