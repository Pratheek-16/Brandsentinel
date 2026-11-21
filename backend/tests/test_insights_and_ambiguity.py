import datetime
import uuid
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.db import session, models
from backend.app.core.security import create_access_token


@pytest.fixture
def insights_test_setup():
    db = session.SessionLocal()
    unique_suffix = uuid.uuid4().hex[:6]

    # 1. Create Workspace
    ws = models.Workspace(name=f"AmbiguityLab_{unique_suffix}", confidential_tier="low")
    db.add(ws)
    db.flush()

    # 2. Create Admin and Creator users
    admin = models.User(
        email=f"admin_{unique_suffix}@test.local",
        password_hash="pw",
        role=models.RoleEnum.admin,
        workspace_id=ws.id,
    )
    creator = models.User(
        email=f"creator_{unique_suffix}@test.local",
        password_hash="pw",
        role=models.RoleEnum.creator,
        workspace_id=ws.id,
    )
    db.add_all([admin, creator])
    db.flush()

    # 3. Create active KB Version
    kb = models.KBVersion(
        workspace_id=ws.id,
        label="Guidelines v1.0",
        created_by=admin.id,
        is_active=True,
    )
    db.add(kb)
    db.flush()

    # 4. Signal 1 setup: High Dismissal Rule
    amb_rule = models.Rule(
        kb_version_id=kb.id,
        code="NF-TONE-AMB",
        category="tone",
        text="Never use exclamation marks or hype words.",
        severity_default="minor",
    )
    db.add(amb_rule)

    # 5. Signal 2 setup: Conflicting Terms and Conflicting Facts
    term1 = models.Term(
        kb_version_id=kb.id,
        preferred="NovaPulse Band",
        banned=["PulseTracker", "OldBand"],
    )
    term2 = models.Term(
        kb_version_id=kb.id,
        preferred="PulseTracker",  # Conflict! PulseTracker is banned in term1 but preferred here!
        banned=["VintageTracker"],
    )
    db.add_all([term1, term2])

    now = datetime.datetime.utcnow()
    fact1 = models.Fact(
        kb_version_id=kb.id,
        code="FACT-BATTERY-A",
        key="battery_life",
        value="10",
        unit="days",
        valid_from=now - datetime.timedelta(days=30),
        valid_to=now + datetime.timedelta(days=30),
    )
    fact2 = models.Fact(
        kb_version_id=kb.id,
        code="FACT-BATTERY-B",
        key="battery_life",
        value="14",  # Conflict! 10 vs 14 days with overlapping date range
        unit="days",
        valid_from=now - datetime.timedelta(days=10),
        valid_to=now + datetime.timedelta(days=50),
    )
    db.add_all([fact1, fact2])

    # 6. Signal 3 setup: Stale (expired) Fact
    stale_fact = models.Fact(
        kb_version_id=kb.id,
        code="FACT-EXPIRED",
        key="water_resistance",
        value="50m",
        valid_from=now - datetime.timedelta(days=100),
        valid_to=now - datetime.timedelta(days=5),  # Expired 5 days ago!
    )
    db.add(stale_fact)

    # 7. Create Content & ReviewRun to host findings
    content = models.Content(
        workspace_id=ws.id,
        creator_id=creator.id,
        title="Ambiguity Test Draft",
        type="text",
        status="revising",
    )
    db.add(content)
    db.flush()

    c_version = models.ContentVersion(
        content_id=content.id,
        version_no=1,
        text_body="Check out our pulse tracker! Amazing performance!",
        content_hash="dummy_hash_123",
        created_by=creator.id,
    )
    db.add(c_version)
    db.flush()

    run = models.ReviewRun(
        version_id=c_version.id,
        kb_version_id=kb.id,
        provider="mock",
        model="mock",
        status="completed",
    )
    db.add(run)
    db.flush()

    # Create 4 findings for NF-TONE-AMB (3 dismissed, 1 accepted = 75% dismissal rate)
    f1 = models.Finding(
        review_run_id=run.id,
        category="tone",
        severity="minor",
        confidence="0.95",
        reason="Tone deviation",
        evidence_id="NF-TONE-AMB",
        span_text="Amazing!",
        span_start=0,
        span_end=8,
        status="dismissed",
        dismissal_reason="Appropriate enthusiasm for consumer social media post",
        source="rule",
    )
    f2 = models.Finding(
        review_run_id=run.id,
        category="tone",
        severity="minor",
        confidence="0.95",
        reason="Tone deviation",
        evidence_id="NF-TONE-AMB",
        span_text="Incredible!",
        span_start=9,
        span_end=19,
        status="dismissed",
        dismissal_reason="Creator deemed it within context",
        source="rule",
    )
    f3 = models.Finding(
        review_run_id=run.id,
        category="tone",
        severity="minor",
        confidence="0.95",
        reason="Tone deviation",
        evidence_id="NF-TONE-AMB",
        span_text="Super!",
        span_start=20,
        span_end=26,
        status="dismissed",
        dismissal_reason="Personal storytelling context",
        source="rule",
    )
    f4 = models.Finding(
        review_run_id=run.id,
        category="tone",
        severity="minor",
        confidence="0.95",
        reason="Tone deviation",
        evidence_id="NF-TONE-AMB",
        span_text="Extremely!",
        span_start=27,
        span_end=37,
        status="accepted",
        source="rule",
    )

    # 8. Signal 4 setup: AI-vs-human disagreement finding
    ai_finding = models.Finding(
        review_run_id=run.id,
        category="claim",
        severity="major",
        confidence="0.90",
        reason="Claim requires substantiation",
        evidence_id="NF-CLAIM-AI",
        span_text="water resistant in light rain",
        span_start=38,
        span_end=67,
        status="dismissed",
        dismissal_reason="false positive: permissible under technical disclosure exceptions",
        source="ai",
    )
    db.add_all([f1, f2, f3, f4, ai_finding])
    db.commit()

    admin_token = create_access_token(data={"sub": str(admin.id), "workspace_id": ws.id, "role": "admin"})
    ws_id = ws.id
    kb_id = kb.id
    db.close()

    yield {
        "workspace_id": ws_id,
        "kb_id": kb_id,
        "admin_token": admin_token,
        "rule_code": "NF-TONE-AMB",
    }


def test_ambiguity_four_signals(insights_test_setup):
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {insights_test_setup['admin_token']}"}

    res = client.get("/insights/ambiguity", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["health_status"] in ["needs_attention", "critical"]
    assert data["total_ambiguity_signals"] >= 4

    # 1. Verify High Dismissal Rule
    high_dismissal = data["flagged_ambiguous_rules"]
    assert len(high_dismissal) >= 1
    amb_rule = next((r for r in high_dismissal if r["rule_code"] == "NF-TONE-AMB"), None)
    assert amb_rule is not None
    assert amb_rule["total_surfaced"] == 4
    assert amb_rule["dismissed_count"] == 3
    assert amb_rule["dismissal_rate_pct"] == 75.0
    assert "suggested_clarification" in amb_rule

    # 2. Verify Conflicting Items (Terms and Facts)
    conflicts = data["conflicting_items"]
    assert len(conflicts) >= 2
    term_conflict = next((c for c in conflicts if c["signal_type"] == "conflicting_term"), None)
    assert term_conflict is not None
    assert term_conflict["term"].lower() == "pulsetracker"

    fact_conflict = next((c for c in conflicts if c["signal_type"] == "conflicting_fact"), None)
    assert fact_conflict is not None
    assert fact_conflict["key"] == "battery_life"

    # 3. Verify Stale Fact
    stale = data["stale_facts"]
    assert len(stale) >= 1
    expired_fact = next((sf for sf in stale if sf["code"] == "FACT-EXPIRED"), None)
    assert expired_fact is not None
    assert "expired" in expired_fact["warning"].lower()

    # 4. Verify AI-vs-Human Disagreement
    ai_disagreements = data["ai_disagreements"]
    assert len(ai_disagreements) >= 1
    ai_diag = ai_disagreements[0]
    assert ai_diag["signal_type"] == "ai_human_disagreement"
    assert "false positive" in ai_diag["human_dismissal_reason"].lower()


def test_accept_clarification_activates_new_kb_version(insights_test_setup):
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {insights_test_setup['admin_token']}"}

    clarified_wording = (
        "Do not use sensational hype words in external ads. "
        "Permissible in organic creator testimonials and technical logs."
    )
    payload = {
        "signal_type": "high_dismissal",
        "target_code": "NF-TONE-AMB",
        "clarified_text": clarified_wording,
    }

    res = client.post("/insights/accept-clarification", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    old_kb_id = data["old_kb_version_id"]
    new_kb_id = data["new_kb_version_id"]
    assert new_kb_id != old_kb_id

    # Verify directly in DB
    db = session.SessionLocal()
    old_kb = db.query(models.KBVersion).filter(models.KBVersion.id == old_kb_id).first()
    new_kb = db.query(models.KBVersion).filter(models.KBVersion.id == new_kb_id).first()

    assert old_kb.is_active is False
    assert new_kb.is_active is True

    # Verify updated rule exists in new KB with clarified text
    updated_rule = (
        db.query(models.Rule)
        .filter(models.Rule.kb_version_id == new_kb.id, models.Rule.code == "NF-TONE-AMB")
        .first()
    )
    assert updated_rule is not None
    assert updated_rule.text == clarified_wording

    # Verify audit event logged
    audit_evt = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.workspace_id == insights_test_setup["workspace_id"], models.AuditEvent.action == "accept_clarification")
        .first()
    )
    assert audit_evt is not None
    assert audit_evt.entity_id == new_kb.id
    assert audit_evt.hash is not None

    db.close()
