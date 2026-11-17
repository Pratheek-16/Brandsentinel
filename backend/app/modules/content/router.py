import datetime
import os
import uuid
import hashlib
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.config import settings
from ...db import session, models
from ...core.security import get_current_user, require_roles
from ..ai_providers.factory import get_provider
from ..verification import verify_findings
from ..redact import redact_text, restore_text
from ..ingest import ingest_file
from ..audit.chain import log_audit_event
from ..workflow.state_machine import validate_transition, evaluate_escalation

router = APIRouter(prefix="/content", tags=["content"])

class ContentCreateSchema(BaseModel):
    title: str
    type: str = "text"
    channel: Optional[str] = None
    body: Optional[str] = ""

class ApprovalSchema(BaseModel):
    decision: str  # approved | changes_requested | rejected | escalated
    reason: Optional[str] = None

class CommentCreateSchema(BaseModel):
    body: str
    finding_id: Optional[int] = None
    parent_id: Optional[int] = None

@router.post("/", status_code=201)
def create_content(
    payload: ContentCreateSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.creator)),
):
    actual_title = payload.title or "Untitled Draft"
    actual_type = payload.type or "text"
    actual_channel = payload.channel
    actual_body = payload.body or ""

    content = models.Content(
        workspace_id=current_user.workspace_id,
        creator_id=current_user.id,
        title=actual_title,
        type=actual_type,
        channel=actual_channel,
        status="draft",
    )
    db.add(content)
    db.flush()

    content_hash = hashlib.sha256(actual_body.encode()).hexdigest()
    version = models.ContentVersion(
        content_id=content.id,
        version_no=1,
        text_body=actual_body,
        file_ref=None,
        content_hash=content_hash,
        created_by=current_user.id,
    )
    db.add(version)
    db.flush()

    content.current_version_id = version.id
    db.commit()

    log_audit_event(
        db=db,
        workspace_id=current_user.workspace_id,
        actor_id=current_user.id,
        action="content.created",
        entity="Content",
        entity_id=content.id,
        payload={"title": content.title, "type": content.type},
    )

    return {
        "content_id": content.id,
        "version_id": version.id,
        "title": content.title,
        "workspace_id": content.workspace_id,
        "status": content.status,
    }

@router.post("/upload", status_code=201)
def upload_content(
    title: str = Form(...),
    type: str = Form("text"),
    channel: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.creator)),
):
    os.makedirs("uploads", exist_ok=True)
    data = file.file.read()
    fname = f"uploads/{uuid.uuid4().hex}_{file.filename}"
    with open(fname, "wb") as f:
        f.write(data)
    file_ref = fname
    extracted_text, detected_type = ingest_file(data, type)
    actual_body = extracted_text or ""

    content = models.Content(
        workspace_id=current_user.workspace_id,
        creator_id=current_user.id,
        title=title,
        type=type,
        channel=channel,
        status="draft",
    )
    db.add(content)
    db.flush()

    content_hash = hashlib.sha256((actual_body + file_ref).encode()).hexdigest()
    version = models.ContentVersion(
        content_id=content.id,
        version_no=1,
        text_body=actual_body,
        file_ref=file_ref,
        content_hash=content_hash,
        created_by=current_user.id,
    )
    db.add(version)
    db.flush()

    content.current_version_id = version.id
    db.commit()

    log_audit_event(
        db=db,
        workspace_id=current_user.workspace_id,
        actor_id=current_user.id,
        action="content.uploaded",
        entity="Content",
        entity_id=content.id,
        payload={"title": content.title, "type": content.type, "file_ref": file_ref},
    )

    return {
        "content_id": content.id,
        "version_id": version.id,
        "title": content.title,
        "workspace_id": content.workspace_id,
        "status": content.status,
    }

@router.get("/{content_id}")
def get_content(
    content_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    version = (
        db.query(models.ContentVersion)
        .filter(models.ContentVersion.id == content.current_version_id)
        .first()
    )
    return {
        "id": content.id,
        "workspace_id": content.workspace_id,
        "creator_id": content.creator_id,
        "title": content.title,
        "type": content.type,
        "channel": content.channel,
        "status": content.status,
        "version_id": version.id if version else None,
        "text_body": version.text_body if version else None,
    }

@router.post("/{content_id}/review", status_code=202)
def review_content(
    content_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    version = (
        db.query(models.ContentVersion)
        .filter(models.ContentVersion.id == content.current_version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    review = models.ReviewRun(
        version_id=version.id,
        kb_version_id=1,
        provider="mock" if not settings.gemini_api_key else "gemini",
        model=settings.llm_model,
        status="running",
    )
    db.add(review)
    db.commit()

    raw_text = version.text_body or ""

    # Wire Redaction before sending to AI provider
    redacted_text, placeholders, counts = redact_text(raw_text)

    # Invoke AI Provider
    provider = get_provider()
    raw_output = provider.generate_json(prompt=redacted_text, schema={"findings": []}, purpose="review")
    raw_findings = raw_output.get("findings", [])

    # Verify findings against the text sent to provider
    clean_findings = verify_findings(raw_findings, redacted_text)

    # Persist findings
    for f in clean_findings:
        span = f["span"]
        evidence = f.get("evidence", {})
        sugg = f.get("suggestion")
        if isinstance(sugg, dict):
            suggestion_text = sugg.get("text", "")
        else:
            suggestion_text = str(sugg) if sugg else None

        new_finding = models.Finding(
            review_run_id=review.id,
            category=f["category"],
            severity=f["severity"],
            confidence=str(f["confidence"]),
            span_start=span["start"],
            span_end=span["end"],
            span_text=span["text"],
            evidence_type=evidence.get("type"),
            evidence_id=str(evidence.get("id")) if evidence.get("id") else None,
            evidence_quote=evidence.get("quote"),
            reason=f["reason"],
            suggestion_text=suggestion_text,
            claim_status=f.get("claim_status", "n/a"),
        )
        db.add(new_finding)

    # Record AI Usage with redaction details and counts
    usage = models.AIUsage(
        review_run_id=review.id,
        provider=review.provider,
        model=review.model,
        purpose="review",
        segments_sent=len(redacted_text),
        segments_received=len(clean_findings),
        redacted_fields={"placeholders": list(placeholders.keys()), "counts": counts},
        redaction_count=counts["total"],
    )
    db.add(usage)

    # Update review run and content status
    review.status = "completed"
    review.finished_at = datetime.datetime.utcnow()
    content.status = "ai_checked"
    db.commit()

    log_audit_event(
        db=db,
        workspace_id=current_user.workspace_id,
        actor_id=current_user.id,
        action="content.reviewed",
        entity="Content",
        entity_id=content.id,
        payload={"review_id": review.id, "findings_count": len(clean_findings)},
    )

    return {
        "review_id": review.id,
        "status": review.status,
        "redaction_count": counts["total"],
        "redacted_counts": counts,
        "findings": clean_findings,
    }

@router.post("/{content_id}/submit", status_code=200)
def submit_content_for_approval(
    content_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.creator)),
):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    validate_transition(content.status, "submitted")

    # Get latest review findings
    latest_review = (
        db.query(models.ReviewRun)
        .filter(models.ReviewRun.version_id == content.current_version_id)
        .order_by(models.ReviewRun.id.desc())
        .first()
    )
    findings = (
        db.query(models.Finding).filter(models.Finding.review_run_id == latest_review.id).all()
        if latest_review else []
    )
    risk_rules = (
        db.query(models.RiskRule).filter(models.RiskRule.workspace_id == content.workspace_id).all()
    )

    is_escalated, reason = evaluate_escalation(findings, risk_rules)
    if is_escalated:
        content.status = "escalated"
    else:
        content.status = "manager_review"

    db.commit()

    log_audit_event(
        db=db,
        workspace_id=current_user.workspace_id,
        actor_id=current_user.id,
        action="content.submitted",
        entity="Content",
        entity_id=content.id,
        payload={"new_status": content.status, "escalated": is_escalated, "reason": reason},
    )

    return {
        "content_id": content.id,
        "status": content.status,
        "escalated": is_escalated,
        "escalation_reason": reason if is_escalated else None,
    }

@router.post("/{content_id}/approve", status_code=200)
def approve_content(
    content_id: int,
    payload: ApprovalSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.manager, models.RoleEnum.reviewer)),
):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    # No self-approval rule check
    if content.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-approval is prohibited: creator cannot approve their own content",
        )

    # If content was escalated, only reviewer role or admin can sign off
    if content.status == "escalated" and current_user.role != models.RoleEnum.reviewer and current_user.role != models.RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Content is escalated: requires Authorised Reviewer signoff",
        )

    validate_transition(content.status, payload.decision)

    version_id = content.current_version_id or 1
    now = datetime.datetime.utcnow()
    sig_raw = f"{content.id}:{version_id}:{current_user.id}:{payload.decision}:{now.isoformat()}"
    signature_hash = hashlib.sha256(sig_raw.encode()).hexdigest()

    approval = models.Approval(
        content_id=content.id,
        version_id=version_id,
        role=current_user.role.value,
        decision=payload.decision,
        reason=payload.reason,
        decided_by=current_user.id,
        decided_at=now,
        signature_hash=signature_hash,
    )
    db.add(approval)
    content.status = payload.decision
    db.commit()

    log_audit_event(
        db=db,
        workspace_id=current_user.workspace_id,
        actor_id=current_user.id,
        action=f"content.{payload.decision}",
        entity="Content",
        entity_id=content.id,
        payload={
            "decision": payload.decision,
            "signature_hash": signature_hash,
            "reason": payload.reason,
        },
    )

    return {
        "approval_id": approval.id,
        "content_id": content.id,
        "status": content.status,
        "decision": approval.decision,
        "signature_hash": approval.signature_hash,
    }

# --- Comments ---

@router.post("/{content_id}/comments", status_code=201)
def add_comment(
    content_id: int,
    payload: CommentCreateSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    comment = models.Comment(
        content_id=content.id,
        version_id=content.current_version_id or 1,
        finding_id=payload.finding_id,
        author_id=current_user.id,
        body=payload.body,
        parent_id=payload.parent_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    log_audit_event(
        db=db,
        workspace_id=current_user.workspace_id,
        actor_id=current_user.id,
        action="comment.created",
        entity="Comment",
        entity_id=comment.id,
        payload={"content_id": content.id, "finding_id": payload.finding_id},
    )

    return {
        "comment_id": comment.id,
        "content_id": comment.content_id,
        "author_id": comment.author_id,
        "body": comment.body,
        "created_at": comment.created_at.isoformat(),
    }

@router.get("/{content_id}/comments")
def list_comments(
    content_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    return (
        db.query(models.Comment)
        .filter(models.Comment.content_id == content_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )

# --- Claims ---

@router.get("/{content_id}/claims")
def get_claim_ledger(
    content_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    version = (
        db.query(models.ContentVersion)
        .filter(models.ContentVersion.id == content.current_version_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    kb = (
        db.query(models.KBVersion)
        .filter(models.KBVersion.workspace_id == content.workspace_id, models.KBVersion.is_active == True)
        .first()
    )
    active_claims = (
        db.query(models.Claim).filter(models.Claim.kb_version_id == kb.id).all() if kb else []
    )

    from ..claims.ledger import evaluate_claims
    ledger = evaluate_claims(version.text_body or "", active_claims)

    return {
        "content_id": content.id,
        "version_id": version.id,
        "total_claims": len(ledger),
        "approved_count": sum(1 for c in ledger if c["status"] == "approved"),
        "missing_disclaimer_count": sum(1 for c in ledger if c["status"] == "missing_disclaimer"),
        "expired_count": sum(1 for c in ledger if c["status"] == "expired"),
        "unsupported_count": sum(1 for c in ledger if c["status"] == "unsupported"),
        "claims": ledger,
    }
