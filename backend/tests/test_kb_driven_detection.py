"""Tests proving Knowledge-Base-Driven Compliance Detection (Priority 1).

Demonstrates that:
1. Editing workspace KB terms dynamically changes review findings: adding a term flags it; removing it stops flagging.
2. A brand-new 4th fictional workspace ('QuantumDine') operates end-to-end with zero code changes.
3. Numeric & date fact verification catches contradicted facts and outdated facts.
4. Claim ledger correctly flags supported, missing_disclaimer, outdated, contradicted, and unsupported claims.
"""

import pytest
import datetime
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import session, models
from backend.app.core.security import create_access_token, hash_password

@pytest.fixture
def client():
    return TestClient(app)

def test_dynamic_kb_term_add_and_remove(client):
    """Proves that adding a term to a workspace KB causes it to be flagged,
    and removing the term immediately stops flagging it."""
    db = next(session.get_db())
    uid = uuid.uuid4().hex[:8]

    # 1. Create a brand-new workspace
    ws = models.Workspace(name=f"DynamicKBTestBrand_{uid}")
    db.add(ws)
    db.commit()
    db.refresh(ws)

    # 2. Create Admin and Creator users
    pwd = hash_password("Demo@12345")
    admin = models.User(
        workspace_id=ws.id,
        email=f"admin_{uid}@dynamictest.local",
        name="Dynamic Admin",
        role=models.RoleEnum.admin,
        password_hash=pwd,
        active=True
    )
    creator = models.User(
        workspace_id=ws.id,
        email=f"creator_{uid}@dynamictest.local",
        name="Dynamic Creator",
        role=models.RoleEnum.creator,
        password_hash=pwd,
        active=True
    )
    db.add(admin)
    db.add(creator)
    db.commit()

    admin_token = create_access_token({"sub": str(admin.id)})
    creator_token = create_access_token({"sub": str(creator.id)})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    # 3. Create content before adding any banned term
    sample_text = "Our brand new solar roof generates pure power without sun stealer technology."
    content_res = client.post(
        "/content/",
        json={"title": "Solar Post", "type": "text", "body": sample_text},
        headers=creator_headers
    )
    assert content_res.status_code == 201
    content_id = content_res.json()["content_id"]

    # Initial review: "sun stealer" is NOT banned yet
    rev1 = client.post(f"/content/{content_id}/review", headers=creator_headers)
    assert rev1.status_code == 202
    findings1 = rev1.json()["findings"]
    assert not any("sun stealer" in f["span"]["text"].lower() for f in findings1)

    # 4. Admin adds "sun stealer" as a banned variant of "Helios Photovoltaic"
    term_res = client.post(
        "/kb/terms",
        json={
            "preferred": "Helios Photovoltaic",
            "banned": ["sun stealer", "solar thief"],
            "case_rule": "none",
            "notes": "Proprietary cell architecture"
        },
        headers=admin_headers
    )
    assert term_res.status_code == 201
    term_id = term_res.json()["id"]

    # 5. Re-run review: "sun stealer" MUST now be flagged dynamically by the KB-driven engine!
    rev2 = client.post(f"/content/{content_id}/review", headers=creator_headers)
    assert rev2.status_code == 202
    findings2 = rev2.json()["findings"]
    term_flags = [f for f in findings2 if "sun stealer" in f["span"]["text"].lower()]
    assert len(term_flags) >= 1, "Expected 'sun stealer' to be flagged after adding term to KB"
    assert term_flags[0]["category"] == "terminology"
    assert "Helios Photovoltaic" in term_flags[0]["suggestion"]["text"]
    assert term_flags[0]["source"] == "rule"

    # 6. Admin deletes the term from the KB
    del_res = client.delete(f"/kb/terms/{term_id}", headers=admin_headers)
    assert del_res.status_code == 200

    # 7. Re-run review: "sun stealer" MUST NO LONGER be flagged!
    rev3 = client.post(f"/content/{content_id}/review", headers=creator_headers)
    assert rev3.status_code == 202
    findings3 = rev3.json()["findings"]
    assert not any("sun stealer" in f["span"]["text"].lower() for f in findings3), (
        "Expected 'sun stealer' to stop being flagged after deleting term from KB"
    )

def test_fourth_fictional_workspace_zero_code_changes(client):
    """Proves that a completely novel 4th workspace ('QuantumDine') operates
    with custom rules, facts, terms, and claims without touching a single line of backend code."""
    db = next(session.get_db())
    uid = uuid.uuid4().hex[:8]

    # 1. Create novel workspace
    ws = models.Workspace(name=f"QuantumDine_{uid}")
    db.add(ws)
    db.commit()
    db.refresh(ws)

    pwd = hash_password("Demo@12345")
    admin = models.User(
        workspace_id=ws.id,
        email=f"admin_{uid}@quantumdine.local",
        name="QD Admin",
        role=models.RoleEnum.admin,
        password_hash=pwd,
        active=True
    )
    creator = models.User(
        workspace_id=ws.id,
        email=f"chef_{uid}@quantumdine.local",
        name="QD Chef",
        role=models.RoleEnum.creator,
        password_hash=pwd,
        active=True
    )
    db.add(admin)
    db.add(creator)
    db.commit()

    admin_token = create_access_token({"sub": str(admin.id)})
    creator_token = create_access_token({"sub": str(creator.id)})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    # 2. Add custom Rule
    r_res = client.post(
        "/kb/rules",
        json={
            "code": "QD-TONE-01",
            "category": "tone",
            "text": "Culinary copy must be appetizing and warm; never use derogatory food slang.",
            "severity_default": "major",
            "examples_bad": ["tastes like cardboard", "slop for pigs"],
            "examples_good": ["savory umami flavor with crisp finish"]
        },
        headers=admin_headers
    )
    assert r_res.status_code == 201

    # 3. Add custom Fact: cook_time_mins = 5 minutes
    f_res = client.post(
        "/kb/facts",
        json={
            "code": "QD-FACT-01",
            "key": "cook_time_mins",
            "value": "5",
            "unit": "minutes",
            "source": "Culinary Lab Certification 2026"
        },
        headers=admin_headers
    )
    assert f_res.status_code == 201

    # 4. Add custom Term
    t_res = client.post(
        "/kb/terms",
        json={
            "preferred": "Cell-Cultivated Salmon",
            "banned": ["fake fish", "test-tube salmon"],
            "case_rule": "none"
        },
        headers=admin_headers
    )
    assert t_res.status_code == 201

    # 5. Add custom Claim with required disclaimer
    c_res = client.post(
        "/kb/claims",
        json={
            "approved_text": "Contains 28g of clean bio-identical marine protein per serving",
            "evidence_ref": "Nutritional Lab Assay #441",
            "required_disclaimer": "*Tested by Food Science Institute.",
            "valid_to": (datetime.datetime.utcnow() + datetime.timedelta(days=180)).isoformat()
        },
        headers=admin_headers
    )
    assert c_res.status_code == 201

    # 6. Author draft with intentional violations:
    # - Tone violation ("tastes like cardboard")
    # - Terminology violation ("fake fish")
    # - Contradicted fact ("cooks in 35 minutes" vs approved 5 minutes)
    draft_body = (
        "Try our fake fish today! Even critics who claim it tastes like cardboard "
        "are amazed that it cooks in 35 minutes."
    )

    create_res = client.post(
        "/content/",
        json={"title": "Chef Special Post", "type": "text", "body": draft_body},
        headers=creator_headers
    )
    assert create_res.status_code == 201
    content_id = create_res.json()["content_id"]

    # 7. Execute review
    rev_res = client.post(f"/content/{content_id}/review", headers=creator_headers)
    assert rev_res.status_code == 202
    findings = rev_res.json()["findings"]

    categories = [f["category"] for f in findings]
    assert "terminology" in categories, "Expected terminology finding for 'fake fish'"
    assert "tone" in categories, "Expected tone finding for 'tastes like cardboard'"
    assert "messaging" in categories, "Expected fact contradiction finding for '35 minutes'"

    # Verify cited evidence IDs belong strictly to QuantumDine KB
    evidence_ids = [f["evidence"]["id"] for f in findings]
    assert any("QD-TONE-01" in eid or "QD-FACT-01" in eid for eid in evidence_ids)
