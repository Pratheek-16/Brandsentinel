import pytest
import datetime
from backend.app.core.datetime_utils import utc_now
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import session, models
from backend.app.core.config import settings
from backend.app.core.security import create_access_token, hash_password
from backend.app.modules.ai_providers.vector_store import VectorStore, cosine_similarity
from backend.app.modules.ai_providers.factory import get_provider
from backend.app.modules.ai_providers.mock import MockProvider
from backend.app.modules.ai_providers.gemini import GeminiProvider

def test_vector_store_retrieval_unit():
    store = VectorStore()
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    v_query = [0.9, 0.1, 0.0]

    store.upsert("rule-1", v1, {"text": "Tone rule 1"})
    store.upsert("rule-2", v2, {"text": "Logo rule 2"})

    results = store.query(v_query, top_k=2)
    assert len(results) == 2
    assert results[0]["id"] == "rule-1"
    assert results[0]["score"] > 0.9
    assert results[1]["id"] == "rule-2"
    assert results[1]["score"] < 0.2

def test_ai_provider_factory():
    # When GEMINI_API_KEY is empty -> MockProvider
    original_key = settings.gemini_api_key
    try:
        settings.gemini_api_key = ""
        p = get_provider()
        assert isinstance(p, MockProvider)

        # When GEMINI_API_KEY is set -> GeminiProvider
        settings.gemini_api_key = "test_gemini_api_key_12345"
        p2 = get_provider()
        assert isinstance(p2, GeminiProvider)
    finally:
        settings.gemini_api_key = original_key

def test_claim_ledger_evaluation():
    client = TestClient(app)
    db = next(session.get_db())

    ws = db.query(models.Workspace).filter(models.Workspace.name == "ClaimsTestWS").first()
    if not ws:
        ws = models.Workspace(name="ClaimsTestWS")
        db.add(ws)
        db.commit()
        db.refresh(ws)

    creator = db.query(models.User).filter(models.User.email == "claims_creator@test.local").first()
    if not creator:
        creator = models.User(
            workspace_id=ws.id,
            email="claims_creator@test.local",
            name="Claims Creator",
            role=models.RoleEnum.creator,
            password_hash=hash_password("Demo@12345"),
            active=True,
        )
        db.add(creator)
        db.commit()
        db.refresh(creator)

    kb = db.query(models.KBVersion).filter(models.KBVersion.workspace_id == ws.id, models.KBVersion.is_active == True).first()
    if not kb:
        kb = models.KBVersion(workspace_id=ws.id, label="v1.0.0", is_active=True)
        db.add(kb)
        db.commit()
        db.refresh(kb)

    # 1. Approved claim with required disclaimer
    claim_valid = models.Claim(
        kb_version_id=kb.id,
        approved_text="Clinically validated 99.4% uptime reduction in downtime",
        evidence_ref="SOC2 Audit 2025",
        required_disclaimer="*Verified by independent audit.",
        valid_to=utc_now() + datetime.timedelta(days=365),
    )
    # 2. Expired claim
    claim_expired = models.Claim(
        kb_version_id=kb.id,
        approved_text="Rated #1 best fitness tracker in 2023",
        evidence_ref="Fitness Awards 2023",
        required_disclaimer=None,
        valid_to=utc_now() - datetime.timedelta(days=100),
    )
    db.add(claim_valid)
    db.add(claim_expired)
    db.commit()

    token = create_access_token({"sub": str(creator.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Content with:
    # A) Valid claim WITH disclaimer
    # B) Valid claim WITHOUT disclaimer
    # C) Expired claim
    # D) Unsupported promotional guarantee claim
    content_body = (
        "Case A: Clinically validated 99.4% uptime reduction in downtime. *Verified by independent audit.\n"
        "Case B: Clinically validated 99.4% uptime reduction in downtime with no disclaimer.\n"
        "Case C: Rated #1 best fitness tracker in 2023.\n"
        "Case D: We offer 100% guarantee fastest results forever.\n"
    )

    create_res = client.post(
        "/content/",
        json={"title": "Claims Test Post", "type": "text", "body": content_body},
        headers=headers,
    )
    assert create_res.status_code == 201
    content_id = create_res.json()["content_id"]

    ledger_res = client.get(
        f"/content/{content_id}/claims",
        headers=headers,
    )
    assert ledger_res.status_code == 200, ledger_res.text
    data = ledger_res.json()
    assert data["total_claims"] >= 3
    assert data["approved_count"] >= 1
    assert data["unsupported_count"] >= 1

    statuses = [c["status"] for c in data["claims"]]
    assert "approved" in statuses
    assert "unsupported" in statuses
