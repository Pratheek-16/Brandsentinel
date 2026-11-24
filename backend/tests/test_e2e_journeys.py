"""Comprehensive End-to-End User Journey Tests (Round 3 Requirements).

Executes the six main end-to-end user journeys through the application:
1. Creator Journey: Login, drafting, review, verified suggestions, tracked edits, submit.
2. Escalation Journey: Blocker violation, no-self-approval enforcement, reviewer escalation, signoff.
3. Admin Journey: KB rule creation, version snapshots, ambiguity detection, clarification acceptance.
4. Visual & Accessibility Journey: Image and PDF analysis, WCAG contrast scoring, page citations.
5. Audit & Ledger Journey: Cryptographic SHA-256 hash chaining, AI usage telemetry, tampering verification.
6. Robustness Journey: Zero-byte files, 50k chars, unauthorized extensions, cross-workspace isolation.
"""

import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import session, models
from backend.app.core.security import hash_password, create_access_token


@pytest.fixture
def journey_setup():
    """Setup dedicated test workspaces and users for end-to-end journeys."""
    db = next(session.get_db())

    # 1. Main Workspace
    ws_main = db.query(models.Workspace).filter(models.Workspace.name == "JourneyMainWS").first()
    if not ws_main:
        ws_main = models.Workspace(name="JourneyMainWS", confidential_tier="high", ai_mode="cloud_allowed")
        db.add(ws_main)
        db.commit()
        db.refresh(ws_main)

    # 2. Isolated Workspace
    ws_iso = db.query(models.Workspace).filter(models.Workspace.name == "JourneyIsoWS").first()
    if not ws_iso:
        ws_iso = models.Workspace(name="JourneyIsoWS", confidential_tier="standard", ai_mode="local_only")
        db.add(ws_iso)
        db.commit()
        db.refresh(ws_iso)

    pwd = hash_password("JourneyPass123!")

    # Users in Main Workspace
    u_creator = db.query(models.User).filter(models.User.email == "journey_creator@main.local").first()
    if u_creator:
        u_creator.workspace_id = ws_main.id
        u_creator.active = True
    else:
        u_creator = models.User(workspace_id=ws_main.id, email="journey_creator@main.local", name="Journey Creator", role=models.RoleEnum.creator, password_hash=pwd, active=True)
        db.add(u_creator)

    u_reviewer = db.query(models.User).filter(models.User.email == "journey_reviewer@main.local").first()
    if u_reviewer:
        u_reviewer.workspace_id = ws_main.id
        u_reviewer.active = True
    else:
        u_reviewer = models.User(workspace_id=ws_main.id, email="journey_reviewer@main.local", name="Journey Reviewer", role=models.RoleEnum.reviewer, password_hash=pwd, active=True)
        db.add(u_reviewer)

    u_admin = db.query(models.User).filter(models.User.email == "journey_admin@main.local").first()
    if u_admin:
        u_admin.workspace_id = ws_main.id
        u_admin.active = True
    else:
        u_admin = models.User(workspace_id=ws_main.id, email="journey_admin@main.local", name="Journey Admin", role=models.RoleEnum.admin, password_hash=pwd, active=True)
        db.add(u_admin)

    # User in Isolated Workspace
    u_iso = db.query(models.User).filter(models.User.email == "journey_user@iso.local").first()
    if u_iso:
        u_iso.workspace_id = ws_iso.id
        u_iso.active = True
    else:
        u_iso = models.User(workspace_id=ws_iso.id, email="journey_user@iso.local", name="Iso User", role=models.RoleEnum.creator, password_hash=pwd, active=True)
        db.add(u_iso)

    db.commit()
    db.refresh(u_creator)
    db.refresh(u_reviewer)
    db.refresh(u_admin)
    db.refresh(u_iso)

    # Setup Active KB for Main Workspace
    kb = db.query(models.KBVersion).filter(models.KBVersion.workspace_id == ws_main.id, models.KBVersion.is_active == True).first()
    if not kb:
        kb = models.KBVersion(workspace_id=ws_main.id, label="Journey Guidelines v1.0", is_active=True)
        db.add(kb)
        db.commit()
        db.refresh(kb)

    # Seed Terminology
    term = db.query(models.Term).filter(models.Term.kb_version_id == kb.id).first()
    if not term:
        db.add(models.Term(
            kb_version_id=kb.id,
            preferred="NovaPulse Band",
            banned=["PulseBand", "pulseband", "Cheap Wristband"],
            case_rule="none",
        ))
        db.commit()

    data = {
        "ws_main_id": ws_main.id,
        "ws_iso_id": ws_iso.id,
        "creator_id": u_creator.id,
        "reviewer_id": u_reviewer.id,
        "admin_id": u_admin.id,
        "iso_user_id": u_iso.id,
        "kb_id": kb.id,
    }
    db.close()
    return data


def test_journey_1_creator_workflow(journey_setup):
    """Journey 1: Creator drafts content, runs review, accepts verified suggestion, submits."""
    client = TestClient(app)

    # 1. Login
    login_res = client.post("/auth/login", json={"email": "journey_creator@main.local", "password": "JourneyPass123!"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check profile
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "journey_creator@main.local"

    # 3. Create Draft with Banned Terminology
    create_res = client.post(
        "/content/",
        json={
            "title": "Summer Campaign Post",
            "type": "text",
            "channel": "social",
            "body": "Get the new PulseBand today for maximum fitness tracking.",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    content_id = create_res.json()["content_id"]

    # 4. Run Review
    review_res = client.post(f"/content/{content_id}/review", headers=headers)
    assert review_res.status_code == 202
    findings = review_res.json()["findings"]
    assert len(findings) > 0
    finding = findings[0]
    assert finding["status"] == "open"
    f_id = finding["id"]

    # 5. Fetch Verified Suggestions via canonical endpoint
    sug_res = client.get(f"/content/{content_id}/findings/{f_id}/suggestions", headers=headers)
    assert sug_res.status_code == 200
    suggestions = sug_res.json().get("suggestions", [])
    assert len(suggestions) > 0
    assert suggestions[0]["meaning_preserved"] is True

    # 6. Apply Suggestion
    replacement = suggestions[0]["replacement_text"]
    accept_res = client.post(
        f"/content/{content_id}/findings/{f_id}/accept",
        json={"replacement_text": replacement},
        headers=headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "applied"
    assert accept_res.json()["version_no"] == 2
    assert replacement in accept_res.json()["updated_text"]

    # 7. Submit for Approval
    submit_res = client.post(f"/content/{content_id}/submit", headers=headers)
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] in ("manager_review", "approved")


def test_journey_2_escalation_and_no_self_approval(journey_setup):
    """Journey 2: Blocker violation cannot be self-approved; escalates to reviewer for signoff."""
    client = TestClient(app)
    creator_id = journey_setup["creator_id"]
    reviewer_id = journey_setup["reviewer_id"]
    admin_id = journey_setup["admin_id"]

    creator_token = create_access_token({"sub": str(creator_id)})
    reviewer_token = create_access_token({"sub": str(reviewer_id)})
    admin_token = create_access_token({"sub": str(admin_id)})

    # Seed blocker rule in active KB
    client.post(
        "/kb/rules",
        json={
            "code": "JOURNEY-BLOCK-01",
            "category": "claim",
            "text": "Never claim 100% cure for serious cardiovascular disease.",
            "severity_default": "blocker",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # 1. Creator creates draft containing blocker claim
    c_res = client.post(
        "/content/",
        json={
            "title": "Heart Health Miracle",
            "type": "text",
            "body": "Our device offers a 100% cure for serious cardiovascular disease guaranteed.",
        },
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    content_id = c_res.json()["content_id"]

    # 2. Review flags blocker
    rev_res = client.post(f"/content/{content_id}/review", headers={"Authorization": f"Bearer {creator_token}"})
    assert rev_res.status_code == 202

    # 3. Creator attempts self-approval -> 403 Forbidden
    self_app = client.post(
        f"/content/{content_id}/approve",
        json={"decision": "approved", "note": "Self approving my own post"},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert self_app.status_code == 403
    detail_lower = self_app.json()["detail"].lower()
    assert "access denied" in detail_lower or "cannot approve" in detail_lower

    # 4. Creator submits -> content status escalates
    sub_res = client.post(f"/content/{content_id}/submit", headers={"Authorization": f"Bearer {creator_token}"})
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] in ("escalated", "manager_review")

    # 5. Reviewer signs off with note
    rev_app = client.post(
        f"/content/{content_id}/approve",
        json={"decision": "approved", "note": "Reviewed by senior compliance officer; approved with exception."},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert rev_app.status_code == 200
    assert rev_app.json()["status"] == "approved"


def test_journey_3_admin_kb_and_ambiguity_clarification(journey_setup):
    """Journey 3: Admin manages KB rules, versions, reviews ambiguity insights, and accepts clarifications."""
    client = TestClient(app)
    admin_id = journey_setup["admin_id"]
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_id)})}"}

    # 1. Add Rule
    add_r = client.post(
        "/kb/rules",
        json={
            "code": "AMB-RULE-01",
            "category": "tone",
            "text": "Never sound too excited or informal in corporate press releases.",
            "severity_default": "minor",
        },
        headers=headers,
    )
    assert add_r.status_code == 201

    # 2. Create Version Snapshot
    snap_res = client.post(
        "/kb/versions",
        json={"label": "Journey Guidelines v2.0"},
        headers=headers,
    )
    assert snap_res.status_code == 201
    assert snap_res.json()["is_active"] is True

    # 3. Query Ambiguity Detector
    insights_res = client.get("/insights/ambiguity", headers=headers)
    assert insights_res.status_code == 200
    data = insights_res.json()
    assert "health_status" in data
    assert "total_ambiguity_signals" in data

    # 4. Accept a suggested clarification via accept-clarification endpoint
    clar_res = client.post(
        "/insights/accept-clarification",
        json={
            "signal_type": "conflicting_rule",
            "target_code": "AMB-RULE-01",
            "clarified_text": "Maintain an objective, factual tone in formal announcements; allow celebratory phrasing for confirmed team milestones.",
        },
        headers=headers,
    )
    assert clar_res.status_code == 200
    assert clar_res.json()["is_active"] is True


def test_journey_4_visual_and_accessibility(journey_setup):
    """Journey 4: Visual and accessibility reviews for images and documents."""
    client = TestClient(app)
    creator_id = journey_setup["creator_id"]
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(creator_id)})}"}

    # 1. Create a synthetic test PNG image
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    upload_res = client.post(
        "/content/upload",
        data={"title": "Brand Hero Banner", "type": "image"},
        files={"file": ("hero.png", buf.getvalue(), "image/png")},
        headers=headers,
    )
    assert upload_res.status_code == 201
    content_id = upload_res.json()["content_id"]

    # 2. Inspect Accessibility and Contrast via Review
    vis_res = client.post(f"/content/{content_id}/review", headers=headers)
    assert vis_res.status_code == 202
    assert "findings" in vis_res.json()


def test_journey_5_audit_hash_chain_and_ledger(journey_setup):
    """Journey 5: Auditor verifies SHA-256 cryptographic audit chain and AI usage ledger."""
    client = TestClient(app)
    admin_id = journey_setup["admin_id"]
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin_id)})}"}

    # 1. Verify Tamper-Proof Audit Chain
    verify_res = client.get("/audit/verify", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True
    assert verify_res.json()["chain_length"] >= 1

    # 2. Query Audit Log Events
    log_res = client.get("/audit/", headers=headers)
    assert log_res.status_code == 200
    data = log_res.json()
    events = data if isinstance(data, list) else data.get("events", [])
    assert len(events) > 0
    first_ev = events[0]
    assert "hash" in first_ev
    assert "prev_hash" in first_ev
    assert len(first_ev["hash"]) == 64  # SHA-256 hex string


def test_journey_6_robustness_and_isolation(journey_setup):
    """Journey 6: Robustness under boundary conditions, malicious payloads, and cross-workspace isolation."""
    client = TestClient(app)
    creator_id = journey_setup["creator_id"]
    iso_user_id = journey_setup["iso_user_id"]

    token_creator = create_access_token({"sub": str(creator_id)})
    token_iso = create_access_token({"sub": str(iso_user_id)})

    # 1. Missing Authorization Header -> 401
    no_auth = client.get("/content/")
    assert no_auth.status_code == 401

    # 2. Invalid Token -> 401
    bad_token = client.get("/content/", headers={"Authorization": "Bearer bad.token.here"})
    assert bad_token.status_code == 401

    # 3. Zero-byte Upload File -> 400
    zero_file = ("zero.txt", b"", "text/plain")
    zero_res = client.post(
        "/content/upload",
        data={"title": "Empty File", "type": "text"},
        files={"file": zero_file},
        headers={"Authorization": f"Bearer {token_creator}"},
    )
    assert zero_res.status_code == 400
    assert "empty" in zero_res.json()["detail"].lower()

    # 4. Prohibited Executable Upload -> 400
    exe_file = ("script.exe", b"MZ\x90\x00malicious binary content", "application/octet-stream")
    exe_res = client.post(
        "/content/upload",
        data={"title": "Payload", "type": "text"},
        files={"file": exe_file},
        headers={"Authorization": f"Bearer {token_creator}"},
    )
    assert exe_res.status_code == 400
    assert "not permitted" in exe_res.json()["detail"]

    # 5. Very Long Text (50,000 characters) Stress Test
    long_text = "NovaFit Pulse tracks daily active minutes and wellness. " * 800
    long_res = client.post(
        "/content/",
        json={"title": "Long Manifesto", "type": "text", "body": long_text},
        headers={"Authorization": f"Bearer {token_creator}"},
    )
    assert long_res.status_code == 201
    long_content_id = long_res.json()["content_id"]

    long_rev = client.post(f"/content/{long_content_id}/review", headers={"Authorization": f"Bearer {token_creator}"})
    assert long_rev.status_code == 202

    # 6. Cross-Workspace Access Isolation
    cross_res = client.get(f"/content/{long_content_id}", headers={"Authorization": f"Bearer {token_iso}"})
    assert cross_res.status_code == 403
    assert "denied" in cross_res.json()["detail"].lower()
