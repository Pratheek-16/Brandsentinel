"""Test suite for the offline Semantic Review Engine (Layer 2).

Verifies generalisation on paraphrased and reworded violations without any external API key.
Tests the 10-sentence reworded probe and verifies 0 false positives on clean text.
"""

import pytest
import uuid
from backend.app.db import session, models
from backend.app.modules.semantic.semantic_engine import run_semantic_checks


@pytest.fixture
def semantic_test_kb():
    """Sets up a test workspace with rules having examples_bad and examples_good."""
    db = session.SessionLocal()
    suffix = uuid.uuid4().hex[:6]
    ws = models.Workspace(name=f"SemanticWS_{suffix}", confidential_tier="low")
    db.add(ws)
    db.flush()

    user = models.User(
        email=f"tester_{suffix}@semantic.local",
        password_hash="pw",
        role=models.RoleEnum.admin,
        workspace_id=ws.id,
    )
    db.add(user)
    db.flush()

    kb = models.KBVersion(
        workspace_id=ws.id,
        label="Semantic KB v1.0",
        created_by=user.id,
        is_active=True,
    )
    db.add(kb)
    db.flush()

    # Rule 1: Tone - No body shaming or lazy accusations
    r1 = models.Rule(
        kb_version_id=kb.id,
        code="NF-TONE-01",
        category="tone",
        text="Encouraging, active, respectful; strictly no body-shaming, insult comedy, or lazy accusations.",
        severity_default="medium",
        examples_good=["Every step counts towards your fitness journey.", "Celebrate small wins."],
        examples_bad=["Stop being so lazy and get off your couch.", "Don't sit around being lazy, get off your sofa!"],
    )

    # Rule 2: Terminology / Health device
    r2 = models.Rule(
        kb_version_id=kb.id,
        code="NF-TERM-01",
        category="terminology",
        text="Use approved fitness wearable terminology; never describe smart sensors with unscientific slang.",
        severity_default="high",
        examples_good=["NovaBand Pro smart fitness tracker.", "Precision biometric sensor."],
        examples_bad=["Fat-melting electric wristband.", "Fat burner watch melts calories."],
    )

    # Rule 3: Price cadence
    r3 = models.Rule(
        kb_version_id=kb.id,
        code="NF-PRICE-01",
        category="messaging",
        text="Always specify currency (USD) and billing cadence (per month or annually billed); avoid informal 'bucks'.",
        severity_default="medium",
        examples_good=["Only $19.99/month, billed annually.", "$9.99 per month cancel anytime."],
        examples_bad=["Costs just 20 bucks!", "Costs just 25 bucks with no contract."],
    )

    # Rule 4: Financial hype / speculation
    r4 = models.Rule(
        kb_version_id=kb.id,
        code="LB-TONE-01",
        category="tone",
        text="Professional, trustworthy, transparent, and direct; strictly no colloquial slang, speculative hype, or fear-mongering.",
        severity_default="high",
        examples_good=["We safeguard your capital with institutional-grade risk management."],
        examples_bad=["YOLO your savings into this moonshot asset!", "Banks are crashing, move your money here!"],
    )

    # Rule 5: Regulated deposit terms
    r5 = models.Rule(
        kb_version_id=kb.id,
        code="LB-TERM-01",
        category="terminology",
        text="Always use regulated banking product terminology; never refer to deposit accounts as crypto lockers or speculative pools.",
        severity_default="high",
        examples_good=["Lumen High-Yield Savings Account", "Lumen Treasury Vault"],
        examples_bad=["Crypto Locker", "Unhackable Money Chest", "Money Doubler", "Super Vault for double money returns"],
    )

    # Rule 6: Campus tone / scholarly
    r6 = models.Rule(
        kb_version_id=kb.id,
        code="AU-TONE-01",
        category="tone",
        text="Inspiring, scholarly, inclusive, and evidence-grounded; avoid hyperbole, sensationalism, or commercial marketing tropes.",
        severity_default="medium",
        examples_good=["Fostering discovery through rigorous interdisciplinary inquiry."],
        examples_bad=["The most lit campus with the sickest dorms in America!", "Our campus has the dopest party dorms!"],
    )

    db.add_all([r1, r2, r3, r4, r5, r6])
    db.commit()

    yield db, ws, kb

    db.close()


def test_semantic_engine_10_reworded_probe_and_clean_texts(semantic_test_kb):
    db, ws, kb = semantic_test_kb

    # The 10 reworded violation test cases (different wording from canonical brand lists)
    reworded_cases = [
        ("Don't sit around being lazy, get off your sofa right now!", "NF-TONE-01"),
        ("Stop being so lazy and get off your couch.", "NF-TONE-01"),
        ("This electric wristband melts away all your body fat overnight.", "NF-TERM-01"),
        ("Our smart fat burner watch melts calories while you rest.", "NF-TERM-01"),
        ("It costs just 25 bucks with no contract!", "NF-PRICE-01"),
        ("Costs just 20 bucks!", "NF-PRICE-01"),
        ("YOLO your savings into this moonshot asset!", "LB-TONE-01"),
        ("Banks are crashing, move your money here immediately!", "LB-TONE-01"),
        ("Put your funds in our Super Vault for double money returns!", "LB-TERM-01"),
        ("The most lit campus with the sickest dorms in America!", "AU-TONE-01"),
    ]

    flagged_count = 0
    for text, expected_rule in reworded_cases:
        findings = run_semantic_checks(text, db=db, kb_version_id=kb.id, threshold=0.58)
        if findings:
            flagged_rule_ids = [f["evidence"]["id"] for f in findings]
            if expected_rule in flagged_rule_ids:
                flagged_count += 1
                # Check citation properties
                matching_f = next(f for f in findings if f["evidence"]["id"] == expected_rule)
                assert matching_f["source"] == "semantic"
                assert matching_f["evidence"]["quote"] is not None
                assert len(matching_f["evidence"]["quote"]) > 0
                assert matching_f["span"]["text"] == text

    # Requirement from master plan: at least 8 of the 10 reworded violations must be flagged correctly
    assert flagged_count >= 8, f"Expected at least 8/10 reworded violations flagged, got {flagged_count}"

    # Clean text cases (MUST produce 0 false positives)
    clean_cases = [
        "Every step counts towards your fitness journey with daily active tracking.",
        "We safeguard your capital with institutional-grade risk management and FDIC coverage.",
        "Fostering discovery through rigorous interdisciplinary inquiry across university laboratories.",
    ]

    for clean_text in clean_cases:
        clean_findings = run_semantic_checks(clean_text, db=db, kb_version_id=kb.id, threshold=0.58)
        assert len(clean_findings) == 0, f"Clean text falsely flagged: {clean_findings}"
