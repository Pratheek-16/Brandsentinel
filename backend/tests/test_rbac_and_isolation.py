import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import session, models
from backend.app.core.security import create_access_token, hash_password

def get_test_users():
    db = next(session.get_db())
    # Workspace 1 (NovaFit)
    ws1 = db.query(models.Workspace).filter(models.Workspace.name == "NovaFit_RBAC").first()
    if not ws1:
        ws1 = models.Workspace(name="NovaFit_RBAC")
        db.add(ws1)
        db.commit()
        db.refresh(ws1)

    # Workspace 2 (Lumen Bank)
    ws2 = db.query(models.Workspace).filter(models.Workspace.name == "LumenBank_RBAC").first()
    if not ws2:
        ws2 = models.Workspace(name="LumenBank_RBAC")
        db.add(ws2)
        db.commit()
        db.refresh(ws2)

    def get_or_create_user(email, role, ws_id):
        u = db.query(models.User).filter(models.User.email == email).first()
        if not u:
            u = models.User(
                workspace_id=ws_id,
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

    creator1_ws1 = get_or_create_user("c1@novafit.local", models.RoleEnum.creator, ws1.id)
    manager_ws1 = get_or_create_user("m1@novafit.local", models.RoleEnum.manager, ws1.id)
    creator_ws2 = get_or_create_user("c2@lumen.local", models.RoleEnum.creator, ws2.id)
    manager_ws2 = get_or_create_user("m2@lumen.local", models.RoleEnum.manager, ws2.id)

    return {
        "ws1": ws1,
        "ws2": ws2,
        "c1_ws1": creator1_ws1,
        "m1_ws1": manager_ws1,
        "c_ws2": creator_ws2,
        "m_ws2": manager_ws2,
    }

def test_rbac_creation_restrictions():
    client = TestClient(app)
    users = get_test_users()

    # Creator can create content
    c1_token = create_access_token({"sub": str(users["c1_ws1"].id)})
    res = client.post(
        "/content/",
        json={"title": "Creator Valid Content", "type": "text", "body": "Draft content text"},
        headers={"Authorization": f"Bearer {c1_token}"},
    )
    assert res.status_code == 201, res.text
    content_id = res.json()["content_id"]

    # Manager without creator role cannot create content directly
    m1_token = create_access_token({"sub": str(users["m1_ws1"].id)})
    res_m = client.post(
        "/content/",
        json={"title": "Manager Content", "type": "text", "body": "Invalid attempt"},
        headers={"Authorization": f"Bearer {m1_token}"},
    )
    assert res_m.status_code == 403, "Manager should be forbidden from creating content"

def test_cross_workspace_isolation():
    client = TestClient(app)
    users = get_test_users()

    # Create content in Workspace 1 by c1
    c1_token = create_access_token({"sub": str(users["c1_ws1"].id)})
    res = client.post(
        "/content/",
        json={"title": "WS1 Confidential Content", "type": "text", "body": "Top secret WS1 data"},
        headers={"Authorization": f"Bearer {c1_token}"},
    )
    assert res.status_code == 201
    content_id = res.json()["content_id"]

    # User in Workspace 2 tries to read it
    c2_token = create_access_token({"sub": str(users["c_ws2"].id)})
    get_res = client.get(
        f"/content/{content_id}",
        headers={"Authorization": f"Bearer {c2_token}"},
    )
    assert get_res.status_code == 403, "Cross workspace read should be rejected"
    assert "Cross-workspace access denied" in get_res.json()["detail"]

    # User in Workspace 2 tries to review it
    rev_res = client.post(
        f"/content/{content_id}/review",
        headers={"Authorization": f"Bearer {c2_token}"},
    )
    assert rev_res.status_code == 403, "Cross workspace review should be rejected"

def test_no_self_approval_and_manager_approval():
    client = TestClient(app)
    users = get_test_users()
    db = next(session.get_db())

    # Create content by c1 in WS1
    c1_token = create_access_token({"sub": str(users["c1_ws1"].id)})
    res = client.post(
        "/content/",
        json={"title": "Approval Test Content", "type": "text", "body": "Ready for approval"},
        headers={"Authorization": f"Bearer {c1_token}"},
    )
    assert res.status_code == 201
    content_id = res.json()["content_id"]

    # Creator attempts to approve their own content (even if they try to call approve)
    approve_self_res = client.post(
        f"/content/{content_id}/approve",
        json={"decision": "approved", "reason": "Self approved"},
        headers={"Authorization": f"Bearer {c1_token}"},
    )
    # Creator role is not manager/reviewer so returns 403 role check
    assert approve_self_res.status_code == 403

    # Now simulate a user with manager role who also created the content
    manager_creator = users["m1_ws1"]
    content_by_manager = models.Content(
        workspace_id=users["ws1"].id,
        creator_id=manager_creator.id,
        title="Manager Authored Content",
        type="text",
        status="ai_checked",
    )
    db.add(content_by_manager)
    db.commit()
    db.refresh(content_by_manager)

    # Manager attempts to approve their own content -> fails with self-approval forbidden
    m1_token = create_access_token({"sub": str(manager_creator.id)})
    self_app_res = client.post(
        f"/content/{content_by_manager.id}/approve",
        json={"decision": "approved", "reason": "Self approving manager"},
        headers={"Authorization": f"Bearer {m1_token}"},
    )
    assert self_app_res.status_code == 403
    assert "Self-approval is prohibited" in self_app_res.json()["detail"]

    # Another manager or reviewer in the same workspace approves it
    reviewer_ws1 = db.query(models.User).filter(models.User.email == "reviewer1@novafit.local").first()
    if not reviewer_ws1:
        reviewer_ws1 = models.User(
            workspace_id=users["ws1"].id,
            email="reviewer1@novafit.local",
            name="Reviewer One",
            role=models.RoleEnum.reviewer,
            password_hash=hash_password("Demo@12345"),
            active=True,
        )
        db.add(reviewer_ws1)
        db.commit()
        db.refresh(reviewer_ws1)

    rev1_token = create_access_token({"sub": str(reviewer_ws1.id)})
    valid_app_res = client.post(
        f"/content/{content_by_manager.id}/approve",
        json={"decision": "approved", "reason": "Reviewed and verified"},
        headers={"Authorization": f"Bearer {rev1_token}"},
    )
    assert valid_app_res.status_code == 200, valid_app_res.text
    data = valid_app_res.json()
    assert data["status"] == "approved"
    assert data["decision"] == "approved"
    assert "signature_hash" in data
