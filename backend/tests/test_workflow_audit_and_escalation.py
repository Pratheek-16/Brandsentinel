import pytest
import datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import session, models
from backend.app.core.security import create_access_token, hash_password
from backend.app.modules.audit.chain import verify_audit_chain

def setup_workflow_users():
    db = next(session.get_db())
    ws = db.query(models.Workspace).filter(models.Workspace.name == "WorkflowWS").first()
    if not ws:
        ws = models.Workspace(name="WorkflowWS")
        db.add(ws)
        db.commit()
        db.refresh(ws)

    def get_or_create_user(email, role):
        u = db.query(models.User).filter(models.User.email == email).first()
        if not u:
            u = models.User(
                workspace_id=ws.id,
                email=email,
                name=email.split("@")[0],
                role=role,
                password_hash=hash_password("Demo@12345"),
                active=True,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
        return u

    creator = get_or_create_user("wf_creator@test.local", models.RoleEnum.creator)
    manager = get_or_create_user("wf_manager@test.local", models.RoleEnum.manager)
    reviewer = get_or_create_user("wf_reviewer@test.local", models.RoleEnum.reviewer)

    return ws, creator, manager, reviewer

def test_workflow_state_machine_and_escalation():
    client = TestClient(app)
    ws, creator, manager, reviewer = setup_workflow_users()

    c_token = create_access_token({"sub": str(creator.id)})
    m_token = create_access_token({"sub": str(manager.id)})
    r_token = create_access_token({"sub": str(reviewer.id)})

    # 1. Creator creates draft
    create_res = client.post(
        "/content/",
        json={"title": "High Risk Campaign", "type": "text", "body": "We guarantee 100% cure for all fatigue."},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert create_res.status_code == 201
    content_id = create_res.json()["content_id"]
    assert create_res.json()["status"] == "draft"

    # 2. Cannot approve while in draft
    invalid_app = client.post(
        f"/content/{content_id}/approve",
        json={"decision": "approved", "reason": "premature"},
        headers={"Authorization": f"Bearer {m_token}"},
    )
    assert invalid_app.status_code == 400
    assert "Invalid state transition" in invalid_app.json()["detail"]

    # 3. AI review completes
    rev_res = client.post(
        f"/content/{content_id}/review",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert rev_res.status_code == 202
    assert rev_res.json()["status"] == "completed"

    # 4. Creator submits for review -> Blocker finding triggers escalation!
    sub_res = client.post(
        f"/content/{content_id}/submit",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["status"] == "escalated"
    assert sub_data["escalated"] is True

    # 5. Manager tries to sign off on escalated content -> 403 Forbidden
    m_app = client.post(
        f"/content/{content_id}/approve",
        json={"decision": "approved", "reason": "Manager override"},
        headers={"Authorization": f"Bearer {m_token}"},
    )
    assert m_app.status_code == 403
    assert "Authorised Reviewer signoff" in m_app.json()["detail"]

    # 6. Authorised Reviewer approves escalated content -> 200 OK
    r_app = client.post(
        f"/content/{content_id}/approve",
        json={"decision": "approved", "reason": "Authorised signoff after medical review"},
        headers={"Authorization": f"Bearer {r_token}"},
    )
    assert r_app.status_code == 200
    assert r_app.json()["status"] == "approved"
    assert r_app.json()["decision"] == "approved"
    assert "signature_hash" in r_app.json()

def test_comments_threading():
    client = TestClient(app)
    ws, creator, manager, _ = setup_workflow_users()
    c_token = create_access_token({"sub": str(creator.id)})
    m_token = create_access_token({"sub": str(manager.id)})

    # Create content
    c_res = client.post(
        "/content/",
        json={"title": "Comment Thread Content", "type": "text", "body": "Check this copy."},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    content_id = c_res.json()["content_id"]

    # Manager leaves comment
    c1_res = client.post(
        f"/content/{content_id}/comments",
        json={"body": "Please qualify the guarantee statement."},
        headers={"Authorization": f"Bearer {m_token}"},
    )
    assert c1_res.status_code == 201
    parent_comment_id = c1_res.json()["comment_id"]

    # Creator replies
    c2_res = client.post(
        f"/content/{content_id}/comments",
        json={"body": "Will revise in next draft version.", "parent_id": parent_comment_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert c2_res.status_code == 201

    # List comments
    list_res = client.get(
        f"/content/{content_id}/comments",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert list_res.status_code == 200
    comments = list_res.json()
    assert len(comments) >= 2
    bodies = [c["body"] for c in comments]
    assert "Please qualify the guarantee statement." in bodies
    assert "Will revise in next draft version." in bodies

def test_audit_log_and_tamper_verification():
    client = TestClient(app)
    ws, creator, manager, _ = setup_workflow_users()
    c_token = create_access_token({"sub": str(creator.id)})
    db = next(session.get_db())

    # 1. Verify audit chain is valid
    audit_res = client.get(
        "/audit/verify",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert audit_res.status_code == 200
    data = audit_res.json()
    assert data["is_valid"] is True
    assert data["total_events"] > 0

    # 2. Tamper with an event in DB to simulate attack / database corruption
    ev = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.workspace_id == ws.id)
        .order_by(models.AuditEvent.id.asc())
        .first()
    )
    original_payload = ev.payload_json
    ev.payload_json = {"tampered": True}
    db.commit()

    # 3. Verify audit chain detects tampering immediately
    tampered_res = client.get(
        "/audit/verify",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert tampered_res.status_code == 200
    tampered_data = tampered_res.json()
    assert tampered_data["is_valid"] is False
    assert "Tampered" in tampered_data["details"]["error"]

    # 4. Restore original payload
    ev.payload_json = original_payload
    db.commit()

    restored_res = client.get(
        "/audit/verify",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert restored_res.json()["is_valid"] is True
