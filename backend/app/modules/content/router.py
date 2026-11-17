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

router = APIRouter(prefix="/content", tags=["content"])

class ContentCreateSchema(BaseModel):
    title: str
    type: str = "text"
    channel: Optional[str] = None
    body: Optional[str] = ""

class ApprovalSchema(BaseModel):
    decision: str  # approved | changes_requested | rejected | escalated
    reason: Optional[str] = None

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
    # Workspace isolation check
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

    # Workspace isolation check
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

    return {
        "review_id": review.id,
        "status": review.status,
        "redaction_count": counts["total"],
        "redacted_counts": counts,
        "findings": clean_findings,
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

    # Workspace isolation check
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    # No self-approval rule check
    if content.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-approval is prohibited: creator cannot approve their own content",
        )

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

    if payload.decision == "approved":
        content.status = "approved"
    elif payload.decision == "changes_requested":
        content.status = "changes_requested"
    elif payload.decision == "escalated":
        content.status = "escalated"
    elif payload.decision == "rejected":
        content.status = "rejected"

    db.commit()
    return {
        "approval_id": approval.id,
        "content_id": content.id,
        "status": content.status,
        "decision": approval.decision,
        "signature_hash": approval.signature_hash,
    }
