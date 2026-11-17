import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import session, models
from backend.app.core.security import create_access_token, hash_password
from backend.app.modules.vision.analyzer import (
    calculate_contrast_ratio,
    delta_e_cielab,
    hex_to_rgb,
    rgb_to_lab,
    analyze_image_brand_consistency,
)
from backend.app.modules.suggestions.engine import get_verified_suggestions, verify_suggestion

def get_improvements_test_user():
    db = next(session.get_db())
    ws = db.query(models.Workspace).filter(models.Workspace.name == "ImprovementsWS").first()
    if not ws:
        ws = models.Workspace(name="ImprovementsWS")
        db.add(ws)
        db.commit()
        db.refresh(ws)

    creator = db.query(models.User).filter(models.User.email == "imp_creator@test.local").first()
    if not creator:
        creator = models.User(
            workspace_id=ws.id,
            email="imp_creator@test.local",
            name="Imp Creator",
            role=models.RoleEnum.creator,
            password_hash=hash_password("Demo@12345"),
            active=True,
        )
        db.add(creator)
        db.commit()
        db.refresh(creator)

    return ws, creator

def test_improvement_1_suggestion_engine_and_actions():
    client = TestClient(app)
    ws, creator = get_improvements_test_user()
    token = create_access_token({"sub": str(creator.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create content with violation
    orig_text = "We promise 100% satisfaction guaranteed on all plans."
    c_res = client.post(
        "/content/",
        json={"title": "Suggestion Test", "type": "text", "body": orig_text},
        headers=headers,
    )
    content_id = c_res.json()["content_id"]

    # 2. Run review
    rev_res = client.post(f"/content/{content_id}/review", headers=headers)
    assert rev_res.status_code == 202
    findings = rev_res.json()["findings"]
    assert len(findings) > 0
    f_id = findings[0]["id"]

    # 3. Unit test suggestion verification
    finding_dict = findings[0]
    verified_suggs = get_verified_suggestions(orig_text, finding_dict)
    assert len(verified_suggs) > 0
    assert verified_suggs[0]["verified"] is True

    # 4. API call to get suggestions
    sugg_res = client.get(f"/content/{content_id}/findings/{f_id}/suggestions", headers=headers)
    assert sugg_res.status_code == 200
    assert len(sugg_res.json()["suggestions"]) > 0

    # 5. Accept suggestion -> creates Version 2
    best_replacement = verified_suggs[0]["replacement_text"]
    accept_res = client.post(
        f"/content/{content_id}/findings/{f_id}/accept",
        json={"replacement_text": best_replacement},
        headers=headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["version_no"] == 2
    assert best_replacement in accept_res.json()["updated_text"]

    # 6. Dismiss another finding for ambiguity testing
    dismiss_res = client.post(
        f"/content/{content_id}/findings/{f_id}/dismiss",
        json={"reason": "Intent is artistic, intentional phrasing."},
        headers=headers,
    )
    assert dismiss_res.status_code == 200
    assert dismiss_res.json()["status"] == "dismissed"

def test_improvement_2_visual_consistency_and_accessibility():
    # 1. Test contrast math directly
    black = (0, 0, 0)
    white = (255, 255, 255)
    ratio_bw = calculate_contrast_ratio(black, white)
    assert ratio_bw == 21.0

    # Low contrast pair: #777777 on #555555
    gray1 = (119, 119, 119)
    gray2 = (85, 85, 85)
    ratio_low = calculate_contrast_ratio(gray1, gray2)
    assert ratio_low < 3.0

    # 2. Test CIELAB Delta-E distance
    lab_blue = rgb_to_lab((0, 85, 255))
    lab_green = rgb_to_lab((16, 185, 129))
    de = delta_e_cielab(lab_blue, lab_green)
    assert de > 20.0  # distinct colors

    # 3. Create synthetic test image (red box on off-brand yellow)
    img = Image.new("RGB", (200, 200), color="#FFFF00") # Yellow background
    # Add off-brand magenta box
    for x in range(50, 150):
        for y in range(50, 150):
            img.putpixel((x, y), (255, 0, 128))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    # Analyze against standard palette (#0055FF, #FFFFFF)
    results = analyze_image_brand_consistency(img_bytes, approved_palette_hex=["#0055FF", "#FFFFFF"])
    assert results["total_issues"] > 0
    assert len(results["palette_findings"]) > 0

    # 4. Test via FastAPI endpoint
    client = TestClient(app)
    _, creator = get_improvements_test_user()
    token = create_access_token({"sub": str(creator.id)})

    api_res = client.post(
        "/vision/analyze",
        files={"file": ("test_banner.png", img_bytes, "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert api_res.status_code == 200
    assert api_res.json()["results"]["total_issues"] > 0

def test_improvement_3_insights_and_ambiguity_detector():
    client = TestClient(app)
    _, creator = get_improvements_test_user()
    token = create_access_token({"sub": str(creator.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Insights summary endpoint
    summary_res = client.get("/insights/summary", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert "content_counts" in summary
    assert "findings_by_category" in summary
    assert "findings_by_severity" in summary

    # 2. Ambiguity detector endpoint
    ambig_res = client.get("/insights/ambiguity", headers=headers)
    assert ambig_res.status_code == 200
    ambig = ambig_res.json()
    assert "flagged_rules" in ambig
    assert len(ambig["flagged_rules"]) > 0
    # Verify ambiguity analysis produces actionable guidance
    rule_entry = ambig["flagged_rules"][0]
    assert "recommendation" in rule_entry
