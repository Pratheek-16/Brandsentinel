import pytest
import datetime
from sqlalchemy.orm import Session
from backend.app.db import session, models

def test_all_remaining_tables_and_crud():
    db = next(session.get_db())

    # 1. Workspace & User
    ws = db.query(models.Workspace).filter(models.Workspace.name == "SchemaTestWS").first()
    if not ws:
        ws = models.Workspace(name="SchemaTestWS", confidential_tier="medium", ai_mode="local")
        db.add(ws)
        db.commit()
        db.refresh(ws)

    user = db.query(models.User).filter(models.User.email == "schema_test@ws.local").first()
    if not user:
        user = models.User(
            workspace_id=ws.id,
            email="schema_test@ws.local",
            name="Schema Test User",
            role=models.RoleEnum.admin,
            password_hash="fakehash",
            active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 2. KBVersion
    kb = models.KBVersion(
        workspace_id=ws.id,
        label="v1.0.0",
        created_by=user.id,
        is_active=True,
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)

    # 3. Rule
    rule = models.Rule(
        kb_version_id=kb.id,
        code="R-TONE-01",
        category="tone",
        text="Maintain professional, empathetic tone.",
        severity_default="major",
        channels=["email", "social"],
        examples_good=["We are here to help."],
        examples_bad=["Figure it out yourself."],
        source_doc="Brand Guidelines 2026",
    )
    db.add(rule)

    # 4. Fact
    fact = models.Fact(
        kb_version_id=kb.id,
        code="F-PRICING-01",
        key="standard_plan_price",
        value="29.99",
        unit="USD/month",
        source="Q1 Pricing Catalog",
        owner="Pricing Committee",
    )
    db.add(fact)

    # 5. Term
    term = models.Term(
        kb_version_id=kb.id,
        preferred="BrandSentinel",
        banned=["Brand-Sentinel", "Brand Sentinel", "brandsentinel"],
        case_rule="ExactMatch",
        notes="Proper noun capitalization required.",
    )
    db.add(term)

    # 6. Claim
    claim = models.Claim(
        kb_version_id=kb.id,
        approved_text="Clinically validated 99.4% uptime.",
        evidence_ref="SOC2 Type II Report 2025",
        required_disclaimer="*Based on third-party audits.",
    )
    db.add(claim)

    # 7. Asset
    asset = models.Asset(
        kb_version_id=kb.id,
        type="palette",
        spec_json={"primary": "#0055FF", "secondary": "#10B981"},
        file_ref="assets/palette.json",
    )
    db.add(asset)

    # 8. RiskRule
    risk_rule = models.RiskRule(
        workspace_id=ws.id,
        condition_json={"min_severity": "blocker", "category": "claim"},
        route_to="reviewer",
        description="Escalate blocker claims to Authorised Reviewer.",
    )
    db.add(risk_rule)

    # 9. Content, ContentVersion, ReviewRun
    content = models.Content(
        workspace_id=ws.id,
        creator_id=user.id,
        title="Schema Check Content",
        type="text",
        status="draft",
    )
    db.add(content)
    db.flush()

    c_version = models.ContentVersion(
        content_id=content.id,
        version_no=1,
        text_body="Some sample content text.",
        content_hash="abc123hash",
        created_by=user.id,
    )
    db.add(c_version)
    db.flush()

    content.current_version_id = c_version.id

    rev_run = models.ReviewRun(
        version_id=c_version.id,
        kb_version_id=kb.id,
        provider="mock",
        model="mock-deterministic",
        status="completed",
    )
    db.add(rev_run)
    db.flush()

    finding = models.Finding(
        review_run_id=rev_run.id,
        category="tone",
        severity="major",
        confidence="0.95",
        span_start=0,
        span_end=4,
        span_text="Some",
        reason="Tone check example",
        suggestion_text="More formal text",
    )
    db.add(finding)
    db.flush()

    # 10. Comment
    comment = models.Comment(
        content_id=content.id,
        version_id=c_version.id,
        finding_id=finding.id,
        author_id=user.id,
        body="Please review this suggested fix.",
    )
    db.add(comment)

    # 11. Approval
    approval = models.Approval(
        content_id=content.id,
        version_id=c_version.id,
        role="admin",
        decision="approved",
        reason="Looks solid.",
        decided_by=user.id,
        signature_hash="mock_signature_hash_123456",
    )
    db.add(approval)

    # 12. AuditEvent
    audit = models.AuditEvent(
        workspace_id=ws.id,
        actor_id=user.id,
        action="content.approved",
        entity="Content",
        entity_id=content.id,
        payload_json={"decision": "approved"},
        prev_hash="GENESIS_HASH",
        hash="CHAINED_HASH_SAMPLE",
    )
    db.add(audit)

    # 13. Job
    job = models.Job(
        type="review_job",
        payload_json={"content_id": content.id},
        status="completed",
        attempts=1,
        result_json={"success": True},
    )
    db.add(job)

    # 14. AIUsage
    usage = models.AIUsage(
        review_run_id=rev_run.id,
        provider="mock",
        model="mock",
        purpose="review",
        segments_sent=100,
        segments_received=1,
        redacted_fields={"placeholders": [], "counts": {"total": 0}},
        redaction_count=0,
    )
    db.add(usage)

    db.commit()

    # Verify lookups from DB
    assert db.query(models.Rule).filter(models.Rule.code == "R-TONE-01").first() is not None
    assert db.query(models.Fact).filter(models.Fact.code == "F-PRICING-01").first() is not None
    assert db.query(models.Term).filter(models.Term.preferred == "BrandSentinel").first() is not None
    assert db.query(models.Claim).filter(models.Claim.approved_text.like("%Clinically%")).first() is not None
    assert db.query(models.Asset).filter(models.Asset.type == "palette").first() is not None
    assert db.query(models.RiskRule).filter(models.RiskRule.workspace_id == ws.id).first() is not None
    assert db.query(models.Comment).filter(models.Comment.content_id == content.id).first() is not None
    assert db.query(models.Approval).filter(models.Approval.content_id == content.id).first() is not None
    assert db.query(models.AuditEvent).filter(models.AuditEvent.action == "content.approved").first() is not None
    assert db.query(models.Job).filter(models.Job.type == "review_job").first() is not None
    assert db.query(models.AIUsage).filter(models.AIUsage.review_run_id == rev_run.id).first() is not None
