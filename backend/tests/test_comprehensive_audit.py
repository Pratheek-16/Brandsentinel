import pytest
import io
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.db import session, models
from backend.app.core.security import create_access_token, hash_password

@pytest.fixture
def audit_test_setup():
    db = next(session.get_db())
    # Create Workspace Alpha
    ws_a = db.query(models.Workspace).filter(models.Workspace.name == "AuditWSAlpha").first()
    if not ws_a:
        ws_a = models.Workspace(name="AuditWSAlpha", confidential_tier="high", ai_mode="cloud_allowed")
        db.add(ws_a)
        db.commit()
        db.refresh(ws_a)

    # Create Workspace Beta
    ws_b = db.query(models.Workspace).filter(models.Workspace.name == "AuditWSBeta").first()
    if not ws_b:
        ws_b = models.Workspace(name="AuditWSBeta", confidential_tier="standard", ai_mode="local_only")
        db.add(ws_b)
        db.commit()
        db.refresh(ws_b)

    pwd = hash_password("AuditSecret123!")

    # Users in Alpha
    u_creator_a = db.query(models.User).filter(models.User.email == "creator@alpha.local").first()
    if not u_creator_a:
        u_creator_a = models.User(workspace_id=ws_a.id, email="creator@alpha.local", name="Alpha Creator", role=models.RoleEnum.creator, password_hash=pwd, active=True)
        db.add(u_creator_a)

    u_manager_a = db.query(models.User).filter(models.User.email == "manager@alpha.local").first()
    if not u_manager_a:
        u_manager_a = models.User(workspace_id=ws_a.id, email="manager@alpha.local", name="Alpha Manager", role=models.RoleEnum.manager, password_hash=pwd, active=True)
        db.add(u_manager_a)

    u_reviewer_a = db.query(models.User).filter(models.User.email == "reviewer@alpha.local").first()
    if not u_reviewer_a:
        u_reviewer_a = models.User(workspace_id=ws_a.id, email="reviewer@alpha.local", name="Alpha Reviewer", role=models.RoleEnum.reviewer, password_hash=pwd, active=True)
        db.add(u_reviewer_a)

    u_admin_a = db.query(models.User).filter(models.User.email == "admin@alpha.local").first()
    if not u_admin_a:
        u_admin_a = models.User(workspace_id=ws_a.id, email="admin@alpha.local", name="Alpha Admin", role=models.RoleEnum.admin, password_hash=pwd, active=True)
        db.add(u_admin_a)

    # User in Beta
    u_creator_b = db.query(models.User).filter(models.User.email == "creator@beta.local").first()
    if not u_creator_b:
        u_creator_b = models.User(workspace_id=ws_b.id, email="creator@beta.local", name="Beta Creator", role=models.RoleEnum.creator, password_hash=pwd, active=True)
        db.add(u_creator_b)

    db.commit()
    db.refresh(u_creator_a)
    db.refresh(u_manager_a)
    db.refresh(u_reviewer_a)
    db.refresh(u_admin_a)
    db.refresh(u_creator_b)

    return {
        "ws_a": ws_a,
        "ws_b": ws_b,
        "creator_a": u_creator_a,
        "manager_a": u_manager_a,
        "reviewer_a": u_reviewer_a,
        "admin_a": u_admin_a,
        "creator_b": u_creator_b,
    }

def test_auth_real_credentials_and_me(audit_test_setup):
    client = TestClient(app)
    # Good login
    res = client.post("/auth/login", json={"email": "creator@alpha.local", "password": "AuditSecret123!"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "creator@alpha.local"
    assert data["user"]["workspace_name"] == "AuditWSAlpha"

    token = data["access_token"]
    # Test /auth/me
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "creator@alpha.local"

    # Bad login
    bad_res = client.post("/auth/login", json={"email": "creator@alpha.local", "password": "WrongPassword!"})
    assert bad_res.status_code == 401

def test_workspace_isolation_and_no_leakage(audit_test_setup):
    client = TestClient(app)
    c_a = audit_test_setup["creator_a"]
    c_b = audit_test_setup["creator_b"]

    token_a = create_access_token({"sub": str(c_a.id)})
    token_b = create_access_token({"sub": str(c_b.id)})

    # Alpha creator creates content
    c_res = client.post(
        "/content/",
        json={"title": "Alpha Confidential Document", "type": "text", "body": "Alpha content only."},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert c_res.status_code == 201
    content_id_a = c_res.json()["content_id"]

    # Beta creator attempts to inspect Alpha content -> 403 Forbidden
    leak_res = client.get(f"/content/{content_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert leak_res.status_code == 403
    assert "Cross-workspace access denied" in leak_res.json()["detail"]

def test_kb_version_cloning_and_activation(audit_test_setup):
    client = TestClient(app)
    admin_a = audit_test_setup["admin_a"]
    token = create_access_token({"sub": str(admin_a.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Add rule and term in active KB
    r_res = client.post(
        "/kb/rules",
        json={"code": "ALPHA-RULE-01", "category": "terminology", "text": "Always write BrandSentinel capitalized."},
        headers=headers,
    )
    assert r_res.status_code == 201

    # Snapshot into new version
    v_res = client.post(
        "/kb/versions",
        json={"label": "Alpha Guidelines v2.0"},
        headers=headers,
    )
    assert v_res.status_code == 201
    v_data = v_res.json()
    assert v_data["is_active"] is True
    assert v_data["cloned_rules"] >= 1

    # List versions
    list_v = client.get("/kb/versions", headers=headers)
    assert list_v.status_code == 200
    assert len(list_v.json()) >= 2

def test_finding_status_lifecycle_and_tracked_edits(audit_test_setup):
    client = TestClient(app)
    c_a = audit_test_setup["creator_a"]
    token = create_access_token({"sub": str(c_a.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Create draft with banned terminology
    c_res = client.post(
        "/content/",
        json={"title": "Device Launch", "type": "text", "body": "Order your brand new Nova Watch today."},
        headers=headers,
    )
    content_id = c_res.json()["content_id"]

    # Review content
    rev_res = client.post(f"/content/{content_id}/review", headers=headers)
    assert rev_res.status_code == 202
    findings = rev_res.json()["findings"]
    assert len(findings) > 0
    f_id = findings[0]["id"]
    assert findings[0]["status"] == "open"

    # Accept suggestion
    accept_res = client.post(
        f"/content/{content_id}/findings/{f_id}/accept",
        json={"replacement_text": "NovaBand Pro smart fitness tracker"},
        headers=headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "applied"
    assert "NovaBand Pro" in accept_res.json()["updated_text"]
    assert accept_res.json()["version_no"] == 2

    # Verify review screen GET does not re-run or duplicate
    get_rev = client.get(f"/content/{content_id}/review", headers=headers)
    assert get_rev.status_code == 200
    assert get_rev.json()["has_review"] is True

def test_upload_security_and_validation(audit_test_setup):
    client = TestClient(app)
    c_a = audit_test_setup["creator_a"]
    token = create_access_token({"sub": str(c_a.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Reject unauthorized executable extension
    bad_file = ("script.exe", b"MZ\x90\x00executable bytes", "application/octet-stream")
    res = client.post(
        "/content/upload",
        data={"title": "Malicious Upload", "type": "text"},
        files={"file": bad_file},
        headers=headers,
    )
    assert res.status_code == 400
    assert "not permitted" in res.json()["detail"]

    # Valid txt upload
    good_file = ("report.txt", b"Safe plain text content for testing.", "text/plain")
    good_res = client.post(
        "/content/upload",
        data={"title": "Clean Report", "type": "text"},
        files={"file": good_file},
        headers=headers,
    )
    assert good_res.status_code == 201
    assert good_res.json()["title"] == "Clean Report"

def test_audit_hash_chain_tamper_verification(audit_test_setup):
    client = TestClient(app)
    admin_a = audit_test_setup["admin_a"]
    token = create_access_token({"sub": str(admin_a.id)})
    headers = {"Authorization": f"Bearer {token}"}

    verify_res = client.get("/audit/verify", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True
    assert "chain_length" in verify_res.json()
