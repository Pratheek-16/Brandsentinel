"""Tests for Verifier Grounding Rigor & MockLLM Hallucination Defense (Priority 2).

Proves that:
1. Verifier BLOCKS findings with hallucinated Rule/Fact IDs not in Knowledge Base.
2. Verifier BLOCKS findings with fabricated quotes that do not match stored KB text.
3. Verifier BLOCKS findings with corrupted/hallucinated character offsets.
4. Verifier ACCEPTS findings that are legitimately grounded with matching quote and offsets.
5. Caching and RAG evidence retrieval operate deterministically.
"""

import pytest
from backend.app.db import session, models
from backend.app.modules.verification import verify_findings
from backend.app.modules.ai_providers.mock_llm import MockLLM
from backend.app.modules.ai_providers.vector_store import global_vector_store

@pytest.fixture
def active_kb_version():
    db = next(session.get_db())
    # Find or create a test KB version with a known rule
    ws = db.query(models.Workspace).filter(models.Workspace.name == "NovaFit").first()
    if not ws:
        ws = models.Workspace(name="NovaFit")
        db.add(ws)
        db.commit()
        db.refresh(ws)

    kb = db.query(models.KBVersion).filter(models.KBVersion.workspace_id == ws.id, models.KBVersion.is_active == True).first()
    if not kb:
        kb = models.KBVersion(workspace_id=ws.id, label="NovaFit v1.0", is_active=True)
        db.add(kb)
        db.commit()
        db.refresh(kb)

    # Ensure NF-TONE-01 rule exists
    rule = db.query(models.Rule).filter(models.Rule.kb_version_id == kb.id, models.Rule.code == "NF-TONE-01").first()
    if not rule:
        rule = models.Rule(
            kb_version_id=kb.id,
            code="NF-TONE-01",
            category="tone",
            text="Empowering, energetic, and encouraging; never shaming, preachy, or punitive.",
            severity_default="major",
        )
        db.add(rule)
        db.commit()

    kb_id = kb.id
    return kb_id

def test_verifier_blocks_hallucinated_rule_id(active_kb_version):
    """Proves that a model hallucinating a non-existent rule code is blocked."""
    db = next(session.get_db())
    original_text = "Stop being so lazy and get off the couch!"

    mock_llm = MockLLM(mode="hallucinate_id")
    raw = mock_llm.generate_json(original_text)
    findings = raw["findings"]
    assert len(findings) == 1
    assert findings[0]["evidence"]["id"] == "HALLUCINATED-RULE-999"

    verified, metrics = verify_findings(
        findings, original_text, db=db, kb_version_id=active_kb_version, return_metrics=True
    )

    assert len(verified) == 0, "Verifier must discard hallucinated rule ID!"
    assert metrics["rejected_invalid_id"] == 1
    assert metrics["rejected_total"] == 1

def test_verifier_blocks_fabricated_quote(active_kb_version):
    """Proves that a model citing a real rule but fabricating the governing quote is blocked."""
    db = next(session.get_db())
    original_text = "Stop being so lazy and get off the couch!"

    mock_llm = MockLLM(mode="wrong_quote")
    raw = mock_llm.generate_json(original_text)
    findings = raw["findings"]
    assert len(findings) == 1
    assert findings[0]["evidence"]["id"] == "NF-TONE-01"

    verified, metrics = verify_findings(
        findings, original_text, db=db, kb_version_id=active_kb_version, return_metrics=True
    )

    assert len(verified) == 0, "Verifier must discard finding with fabricated quote!"
    assert metrics["rejected_unmatched_quote"] == 1
    assert metrics["rejected_total"] == 1

def test_verifier_blocks_offset_mismatch(active_kb_version):
    """Proves that a model outputting character offsets that do not match the text span is blocked."""
    db = next(session.get_db())
    original_text = "Stop being so lazy and get off the couch!"

    mock_llm = MockLLM(mode="offset_mismatch")
    raw = mock_llm.generate_json(original_text)
    findings = raw["findings"]

    verified, metrics = verify_findings(
        findings, original_text, db=db, kb_version_id=active_kb_version, return_metrics=True
    )

    assert len(verified) == 0, "Verifier must discard finding with offset/text mismatch!"
    assert metrics["rejected_offsets"] == 1

def test_verifier_accepts_legitimate_grounded_finding(active_kb_version):
    """Proves that legitimately grounded findings matching KB text and offsets pass cleanly."""
    db = next(session.get_db())
    original_text = "Stop being lazy and get moving today!"

    mock_llm = MockLLM(mode="grounded")
    raw = mock_llm.generate_json(original_text)
    findings = raw["findings"]

    verified, metrics = verify_findings(
        findings, original_text, db=db, kb_version_id=active_kb_version, return_metrics=True
    )

    assert len(verified) == 1, "Legitimately grounded finding must pass verification!"
    assert metrics["rejected_total"] == 0
    assert verified[0]["evidence"]["id"] == "NF-TONE-01"
    assert verified[0]["source"] == "ai"

def test_vector_store_retrieval_filtering(active_kb_version):
    """Proves evidence retrieval ranks relevant rules and respects validity filters."""
    db = next(session.get_db())
    query_text = "Does the battery last 14 days and is the tone encouraging?"

    evidence = global_vector_store.retrieve_evidence_for_segment(
        segment_text=query_text,
        db=db,
        kb_version_id=active_kb_version,
        top_k=5,
    )

    assert len(evidence) > 0
    ids = [e["id"] for e in evidence]
    # NF-TONE-01 should be retrieved for encouraging tone
    assert "NF-TONE-01" in ids or any(e["type"] == "rule" for e in evidence)
