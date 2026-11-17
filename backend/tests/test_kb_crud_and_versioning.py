import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import session, models
from backend.app.core.security import create_access_token, hash_password

def get_kb_test_admin():
    db = next(session.get_db())
    ws = db.query(models.Workspace).filter(models.Workspace.name == "KB_Test_WS").first()
    if not ws:
        ws = models.Workspace(name="KB_Test_WS")
        db.add(ws)
        db.commit()
        db.refresh(ws)

    admin = db.query(models.User).filter(models.User.email == "admin@kbtest.local").first()
    if not admin:
        admin = models.User(
            workspace_id=ws.id,
            email="admin@kbtest.local",
            name="Admin KB",
            role=models.RoleEnum.admin,
            password_hash=hash_password("Demo@12345"),
            active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    creator = db.query(models.User).filter(models.User.email == "creator@kbtest.local").first()
    if not creator:
        creator = models.User(
            workspace_id=ws.id,
            email="creator@kbtest.local",
            name="Creator KB",
            role=models.RoleEnum.creator,
            password_hash=hash_password("Demo@12345"),
            active=True,
        )
        db.add(creator)
        db.commit()
        db.refresh(creator)

    return admin, creator, ws

def test_kb_crud_and_permissions():
    client = TestClient(app)
    admin, creator, ws = get_kb_test_admin()
    admin_token = create_access_token({"sub": str(admin.id)})
    creator_token = create_access_token({"sub": str(creator.id)})

    # Admin creates rule
    rule_data = {
        "code": "R-TONE-101",
        "category": "tone",
        "text": "Always write with uplifting and supportive energy.",
        "severity_default": "major",
        "channels": ["social", "email"],
    }
    res = client.post(
        "/kb/rules",
        json=rule_data,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 201, res.text
    rule_id = res.json()["id"]

    # Creator can read rules
    list_res = client.get(
        "/kb/rules",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert list_res.status_code == 200
    codes = [r["code"] for r in list_res.json()]
    assert "R-TONE-101" in codes

    # Creator cannot create rule
    c_res = client.post(
        "/kb/rules",
        json={"code": "R-FAIL", "category": "tone", "text": "Fail test"},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert c_res.status_code == 403

    # Admin deletes rule
    del_res = client.delete(
        f"/kb/rules/{rule_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_res.status_code == 200

def test_rule_atomisation_and_confirm_import():
    client = TestClient(app)
    admin, _, _ = get_kb_test_admin()
    admin_token = create_access_token({"sub": str(admin.id)})

    raw_guidelines = (
        "# Brand Guidelines 2026\n"
        "- Never use the phrase 'cheap price' or claim 100% guarantee; this is strictly prohibited.\n"
        "- Ensure all digital assets maintain WCAG 2.2 AA contrast ratios.\n"
        "- The standard price for NovaFit Pro is $49/month.\n"
    )

    # 1. Atomise endpoint
    atom_res = client.post(
        "/kb/atomise",
        json={"guidelines_text": raw_guidelines},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert atom_res.status_code == 200
    candidates = atom_res.json()["candidates"]
    assert len(candidates) >= 2
    # Verify atomisation found prohibited claim/tone and accessibility
    categories = [c["category"] for c in candidates]
    assert any(cat in ["claim", "tone"] for cat in categories)

    # 2. Confirm import flow
    confirm_payload = {
        "rules": [
            {
                "code": candidates[0]["code"],
                "category": candidates[0]["category"],
                "text": candidates[0]["text"],
                "severity_default": candidates[0]["severity_default"],
            }
        ],
        "facts": [
            {
                "code": "F-PRICE-001",
                "key": "novafit_pro_price",
                "value": "49",
                "unit": "USD/mo",
            }
        ],
    }
    import_res = client.post(
        "/kb/confirm-import",
        json=confirm_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert import_res.status_code == 201
    assert import_res.json()["saved_rules"] == 1
    assert import_res.json()["saved_facts"] == 1

def test_kb_versioning():
    client = TestClient(app)
    admin, _, ws = get_kb_test_admin()
    admin_token = create_access_token({"sub": str(admin.id)})

    # List versions
    list_v = client.get(
        "/kb/versions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_v.status_code == 200
    initial_count = len(list_v.json())
    initial_version_id = list_v.json()[0]["id"]

    # Create new snapshot version v2.0.0
    new_v_res = client.post(
        "/kb/versions",
        json={"label": "v2.0.0-release"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert new_v_res.status_code == 201
    v2_id = new_v_res.json()["id"]
    assert new_v_res.json()["is_active"] is True

    # Re-activate initial version
    act_res = client.post(
        f"/kb/versions/{initial_version_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert act_res.status_code == 200
    assert act_res.json()["active_version_id"] == initial_version_id
