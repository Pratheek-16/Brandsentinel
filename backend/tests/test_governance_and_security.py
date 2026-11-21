import os
import re
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.db import session, models
from backend.app.core.config import Settings
from backend.app.core.security import create_access_token
from backend.app.modules.redact import (
    redact_text,
    redact_text_with_offsets,
    map_redacted_span_to_original,
    restore_text,
)


def test_indian_pii_redaction():
    text = (
        "Customer Aadhaar: 4321 8765 2109, secondary card: 987654321098. "
        "Tax PAN number ABCDE1234F for billing. "
        "Send refund via UPI user@okaxis or payments@upi. "
        "Bank IFSC code SBIN0001234. "
        "Contact mobile +91 9876543210 or alternate 9876543211. "
        "Email support@example.com."
    )

    redacted, placeholders, counts, offsets = redact_text_with_offsets(text)

    # 1. Verify Aadhaar redacted
    assert counts["aadhaar"] == 2
    assert "4321 8765 2109" not in redacted
    assert "987654321098" not in redacted
    assert "<AADHAAR_1>" in redacted
    assert "<AADHAAR_2>" in redacted

    # 2. Verify PAN redacted
    assert counts["pan"] == 1
    assert "ABCDE1234F" not in redacted
    assert "<PAN_1>" in redacted

    # 3. Verify UPI ID redacted
    assert counts["upi_id"] >= 1
    assert "user@okaxis" not in redacted
    assert "<UPI_ID_1>" in redacted

    # 4. Verify IFSC redacted
    assert counts["ifsc"] == 1
    assert "SBIN0001234" not in redacted
    assert "<IFSC_1>" in redacted

    # 5. Verify Phone redacted
    assert counts["phone"] >= 1
    assert "9876543210" not in redacted

    # 6. Verify Email redacted
    assert counts["email"] == 1
    assert "support@example.com" not in redacted
    assert "<EMAIL_1>" in redacted

    # 7. Test restoration
    restored = restore_text(redacted, placeholders)
    assert restored == text


def test_jwt_secret_startup_protection():
    # Production with missing secret -> must raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        Settings(
            environment="production",
            jwt_secret_key="change-me-in-production-use-a-real-secret-key-at-least-32-chars",
        )
    assert "FATAL SECURITY VIOLATION" in str(exc_info.value)

    # Production with short secret (< 32 chars) -> must raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        Settings(
            environment="production",
            jwt_secret_key="short_insecure_secret_123",
        )
    assert "FATAL SECURITY VIOLATION" in str(exc_info.value)

    # Non-production (development) -> generates secure ephemeral secret with warning
    dev_settings = Settings(environment="development", jwt_secret_key=None)
    assert dev_settings.jwt_secret_key is not None
    assert len(dev_settings.jwt_secret_key) >= 32


def test_ai_ledger_and_governance_export():
    import uuid
    db = session.SessionLocal()
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:6]

    # Setup workspace, user, content, version
    ws = models.Workspace(name=f"GovSecurityLab_{suffix}", confidential_tier="medium")
    db.add(ws)
    db.flush()

    user = models.User(
        email=f"creator_gov_{suffix}@test.local",
        password_hash="pw",
        role=models.RoleEnum.creator,
        workspace_id=ws.id,
    )
    db.add(user)
    db.flush()

    kb = models.KBVersion(
        workspace_id=ws.id,
        label="Guidelines v1.0",
        created_by=user.id,
        is_active=True,
    )
    db.add(kb)
    db.flush()

    content = models.Content(
        workspace_id=ws.id,
        creator_id=user.id,
        title="Q3 Product Announcement",
        type="text",
        status="approved",
    )
    db.add(content)
    db.flush()

    version = models.ContentVersion(
        content_id=content.id,
        version_no=1,
        text_body="Introducing our new pulse tracker with 10 days of battery life.",
        content_hash="mock_hash_987",
        created_by=user.id,
    )
    db.add(version)
    db.flush()

    content.current_version_id = version.id

    run = models.ReviewRun(
        version_id=version.id,
        kb_version_id=kb.id,
        provider="gemini",
        model="gemini-1.5-flash",
        status="completed",
    )
    db.add(run)
    db.flush()

    # Add AIUsage record
    usage = models.AIUsage(
        review_run_id=run.id,
        provider="gemini",
        model="gemini-1.5-flash",
        purpose="review",
        segments_sent=2,
        segments_received=2,
        redaction_count=3,
        redacted_fields=["email", "phone"],
    )
    db.add(usage)

    finding = models.Finding(
        review_run_id=run.id,
        category="terminology",
        severity="minor",
        confidence="0.95",
        reason="Use approved product name",
        evidence_id="NF-TERM-01",
        span_text="pulse tracker",
        span_start=24,
        span_end=37,
        status="accepted",
        source="ai",
    )
    db.add(finding)
    db.commit()

    token = create_access_token({"sub": str(user.id), "workspace_id": ws.id, "role": "creator"})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test GET /content/{id}/ai-ledger
    ledger_res = client.get(f"/content/{content.id}/ai-ledger", headers=headers)
    assert ledger_res.status_code == 200
    ledger_data = ledger_res.json()
    assert ledger_data["content_id"] == content.id
    assert ledger_data["provider"] == "gemini"
    assert ledger_data["model"] == "gemini-1.5-flash"
    assert ledger_data["totals"]["redacted_entities"] == 3
    assert "$" in ledger_data["totals"]["estimated_cost_usd"]
    assert ledger_data["human_governance"]["total_ai_findings"] == 1
    assert ledger_data["human_governance"]["human_accepted_count"] == 1

    # 2. Test GET /content/{id}/export (Markdown)
    export_md = client.get(f"/content/{content.id}/export?format=markdown", headers=headers)
    assert export_md.status_code == 200
    assert "Brand Governance Certificate" in export_md.text
    assert "Verification Signature" in export_md.text
    assert "Q3 Product Announcement" in export_md.text

    # 3. Test GET /content/{id}/export (JSON)
    export_json = client.get(f"/content/{content.id}/export?format=json", headers=headers)
    assert export_json.status_code == 200
    cert_json = export_json.json()
    assert "certificate_id" in cert_json
    assert "cryptographic_verification" in cert_json
    assert cert_json["cryptographic_verification"]["algorithm"] == "SHA-256"
    assert len(cert_json["cryptographic_verification"]["signature"]) == 64

    # 4. Test GET /content/{id}/export (HTML)
    export_html = client.get(f"/content/{content.id}/export?format=html", headers=headers)
    assert export_html.status_code == 200
    assert "<!DOCTYPE html>" in export_html.text

    db.close()
