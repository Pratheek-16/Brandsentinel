import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import session, models
from backend.app.modules.redact import redact_text, restore_text
from backend.app.core.security import create_access_token, hash_password

def test_redact_and_restore_unit():
    raw = (
        "User email is test.user@example.com, phone is 555-234-5678. "
        "Secret token is ghp_123456789012345678901234567890123456 and ssn is 000-12-3456."
    )
    redacted, placeholders, counts = redact_text(raw)
    assert "<EMAIL_1>" in redacted
    assert "<PHONE_1>" in redacted
    assert "<SECRET_1>" in redacted
    assert "<SSN_1>" in redacted
    assert "test.user@example.com" not in redacted
    assert counts["email"] == 1
    assert counts["phone"] == 1
    assert counts["secret"] == 1
    assert counts["ssn"] == 1
    assert counts["total"] == 4

    restored = restore_text(redacted, placeholders)
    assert restored == raw

def test_review_with_redaction_persisted_in_ai_usage():
    client = TestClient(app)
    db = next(session.get_db())

    # Ensure workspace
    ws = db.query(models.Workspace).filter(models.Workspace.name == "RedactTestWorkspace").first()
    if not ws:
        ws = models.Workspace(name="RedactTestWorkspace")
        db.add(ws)
        db.commit()
        db.refresh(ws)

    # Ensure user
    user = db.query(models.User).filter(models.User.email == "creator_redact@test.local").first()
    if not user:
        user = models.User(
            workspace_id=ws.id,
            email="creator_redact@test.local",
            name="Redact Creator",
            role=models.RoleEnum.creator,
            password_hash=hash_password("Demo@12345"),
            active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Create content with PII and guaranteed phrase that triggers deterministic check
    content_text = "Reach me at contact@novafit.local or call 555-888-9999. We guarantee 100% satisfaction guaranteed."
    res = client.post(
        "/content/",
        json={"title": "PII Content", "type": "text", "body": content_text},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    content_id = res.json()["content_id"]

    # Review content
    rev_res = client.post(f"/content/{content_id}/review", headers=headers)
    assert rev_res.status_code == 202, rev_res.text
    data = rev_res.json()
    assert data["status"] == "completed"
    assert data["redaction_count"] == 2
    assert data["redacted_counts"]["email"] == 1
    assert data["redacted_counts"]["phone"] == 1

    # Check database AIUsage record
    review_run_id = data["review_id"]
    usage = db.query(models.AIUsage).filter(models.AIUsage.review_run_id == review_run_id).first()
    assert usage is not None
    assert usage.redaction_count == 2
    assert usage.redacted_fields["counts"]["email"] == 1
    assert usage.redacted_fields["counts"]["phone"] == 1
    assert usage.purpose == "review"
