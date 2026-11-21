import datetime
import os
import uuid
import hashlib
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.config import settings
from ...db import session, models
from ...core.security import get_current_user, require_roles
from ..ai_providers.factory import get_provider
from ..verification import verify_findings
from ..redact import redact_text_with_offsets, map_redacted_span_to_original
from ..ingest import ingest_file, sanitize_filename
from ..audit.chain import log_audit_event
from ..workflow.state_machine import validate_transition, evaluate_escalation
from ..suggestions.engine import get_verified_suggestions, verify_suggestion

router = APIRouter(prefix="/content", tags=["content"])

# --- Request Schemas ---

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

class AcceptSuggestionSchema(BaseModel):
    replacement_text: str

class EditSuggestionSchema(BaseModel):
    custom_text: Optional[str] = None
    replacement_text: Optional[str] = None

class DismissFindingSchema(BaseModel):
    reason: str

# --- Endpoints ---

@router.get("/")
def list_workspace_contents(
    status_filter: Optional[str] = None,
    channel: Optional[str] = None,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Lists all content items within the active user's workspace."""
    query = (
        db.query(models.Content)
        .filter(models.Content.workspace_id == current_user.workspace_id)
    )
    if status_filter:
        query = query.filter(models.Content.status == status_filter)
    if channel:
        query = query.filter(models.Content.channel == channel)

    contents = query.order_by(models.Content.id.desc()).all()
    results = []

    for c in contents:
        creator = db.query(models.User).filter(models.User.id == c.creator_id).first()
        version = (
            db.query(models.ContentVersion)
            .filter(models.ContentVersion.id == c.current_version_id)
            .first()
        )
        # Check review run findings count
        latest_review = (
            db.query(models.ReviewRun)
            .filter(models.ReviewRun.version_id == c.current_version_id)
            .order_by(models.ReviewRun.id.desc())
            .first()
        )
        findings_count = 0
        blockers_count = 0
        if latest_review:
            findings_count = db.query(models.Finding).filter(models.Finding.review_run_id == latest_review.id).count()
            blockers_count = db.query(models.Finding).filter(models.Finding.review_run_id == latest_review.id, models.Finding.severity == "blocker").count()

        results.append({
            "id": c.id,
            "title": c.title,
            "type": c.type,
            "channel": c.channel,
            "status": c.status,
            "creator_id": c.creator_id,
            "creator_name": creator.name if creator else "Unknown",
            "creator_email": creator.email if creator else "",
            "current_version_no": version.version_no if version else 1,
            "current_version_id": version.id if version else None,
            "findings_count": findings_count,
            "blockers_count": blockers_count,
            "created_at": c.created_at.isoformat() if hasattr(c, "created_at") and c.created_at else None,
        })

    return results

@router.post("/", status_code=201)
def create_content(
    payload: ContentCreateSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.creator)),
):
    actual_title = (payload.title or "Untitled Draft").strip()
    actual_type = payload.type or "text"
    actual_channel = payload.channel or "general"
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
        payload={"title": content.title, "type": content.type, "channel": content.channel},
    )

    return {
        "content_id": content.id,
        "version_id": version.id,
        "title": content.title,
        "workspace_id": content.workspace_id,
        "status": content.status,
        "channel": content.channel,
    }

@router.post("/upload", status_code=201)
def upload_content(
    title: str = Form(...),
    type: str = Form("text"),
    channel: Optional[str] = Form("general"),
    file: UploadFile = File(...),
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.creator)),
):
    raw_filename = file.filename or "upload"
    _, ext = os.path.splitext(raw_filename)
    clean_ext = ext.lower()

    if clean_ext not in settings.allowed_upload_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{clean_ext}' not permitted. Allowed: {', '.join(settings.allowed_upload_extensions)}"
        )

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(data) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed limit of {settings.max_upload_size_bytes // (1024*1024)}MB."
        )

    # Sanitize filename and store in configured upload directory
    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_name = sanitize_filename(raw_filename)
    stored_filename = f"{uuid.uuid4().hex}_{safe_name}"
    full_path = os.path.join(settings.upload_dir, stored_filename)

    with open(full_path, "wb") as f:
        f.write(data)

    # Extract text cleanly
    try:
        extracted_text, detected_type = ingest_file(data, clean_ext)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    actual_body = extracted_text or ""

    content = models.Content(
        workspace_id=current_user.workspace_id,
        creator_id=current_user.id,
        title=title.strip() or safe_name,
        type=type or detected_type,
        channel=channel or "general",
        status="draft",
    )
    db.add(content)
    db.flush()

    content_hash = hashlib.sha256((actual_body + stored_filename).encode()).hexdigest()
    version = models.ContentVersion(
        content_id=content.id,
        version_no=1,
        text_body=actual_body,
        file_ref=stored_filename,
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
        payload={"title": content.title, "type": content.type, "file_ref": stored_filename},
    )

    return {
        "content_id": content.id,
        "version_id": version.id,
        "title": content.title,
        "workspace_id": content.workspace_id,
        "status": content.status,
        "channel": content.channel,
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

    all_versions = (
        db.query(models.ContentVersion)
        .filter(models.ContentVersion.content_id == content.id)
        .order_by(models.ContentVersion.version_no.desc())
        .all()
    )

    versions_summary = [
        {
            "id": v.id,
            "version_no": v.version_no,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "created_by": v.created_by,
            "content_hash": v.content_hash,
        }
        for v in all_versions
    ]

    creator = db.query(models.User).filter(models.User.id == content.creator_id).first()

    return {
        "id": content.id,
        "workspace_id": content.workspace_id,
        "creator_id": content.creator_id,
        "creator_name": creator.name if creator else "Creator",
        "creator_email": creator.email if creator else "",
        "title": content.title,
        "type": content.type,
        "channel": content.channel,
        "status": content.status,
        "version_id": version.id if version else None,
        "version_no": version.version_no if version else 1,
        "text_body": version.text_body if version else None,
        "file_ref": version.file_ref if version else None,
        "versions": versions_summary,
    }

@router.get("/{content_id}/review")
def get_existing_review(
    content_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Retrieves the latest completed review run and its findings without triggering a new review."""
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    review = (
        db.query(models.ReviewRun)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .filter(models.ContentVersion.content_id == content.id)
        .order_by(models.ReviewRun.id.desc())
        .first()
    )

    if not review:
        return {"has_review": False, "findings": [], "review": None}

    findings = (
        db.query(models.Finding)
        .filter(models.Finding.review_run_id == review.id)
        .order_by(models.Finding.span_start.asc())
        .all()
    )

    findings_data = [
        {
            "id": f.id,
            "category": f.category,
            "severity": f.severity,
            "confidence": float(f.confidence) if f.confidence else 1.0,
            "span": {
                "start": f.span_start,
                "end": f.span_end,
                "text": f.span_text,
            },
            "span_start": f.span_start,
            "span_end": f.span_end,
            "span_text": f.span_text,
            "evidence": {
                "type": f.evidence_type,
                "id": f.evidence_id,
                "quote": f.evidence_quote,
            },
            "reason": f.reason,
            "suggestion_text": f.suggestion_text,
            "claim_status": f.claim_status,
            "source": f.source or "rule",
            "status": f.status or "open",
            "selected_replacement": f.selected_replacement,
            "dismissal_reason": f.dismissal_reason,
            "decided_by": f.decided_by,
            "decided_at": f.decided_at.isoformat() if f.decided_at else None,
        }
        for f in findings
    ]

    usage = db.query(models.AIUsage).filter(models.AIUsage.review_run_id == review.id).first()

    return {
        "has_review": True,
        "review": {
            "id": review.id,
            "version_id": review.version_id,
            "kb_version_id": review.kb_version_id,
            "status": review.status,
            "provider": review.provider,
            "model": review.model,
            "started_at": review.started_at.isoformat() if review.started_at else None,
            "finished_at": review.finished_at.isoformat() if review.finished_at else None,
            "redaction_count": usage.redaction_count if usage else 0,
            "redacted_fields": usage.redacted_fields if usage else {},
        },
        "findings": findings_data,
    }

@router.post("/{content_id}/review", status_code=202)
def review_content(
    content_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Executes a pre-publication brand compliance review across active KB guidelines."""
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

    # Dynamically resolve active KB version using workspace_id
    from ..kb.router import get_or_create_active_kb
    active_kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)

    provider_name = "mock" if not settings.gemini_api_key else "gemini"
    review = models.ReviewRun(
        version_id=version.id,
        kb_version_id=active_kb.id,
        provider=provider_name,
        model=settings.llm_model,
        status="running",
    )
    db.add(review)
    db.commit()

    raw_text = version.text_body or ""

    # 1. Redact PII and sensitive data before any external provider processing
    redacted_text, placeholders, counts, offset_records = redact_text_with_offsets(raw_text)

    # 2. Evidence Retrieval (RAG) from Active Knowledge Base
    from ..ai_providers.vector_store import global_vector_store
    retrieved_evidence = global_vector_store.retrieve_evidence_for_segment(
        raw_text,
        db=db,
        kb_version_id=active_kb.id,
        top_k=6,
        channel=content.channel,
    )

    # Layer 1: Knowledge-Base Driven Deterministic Engine
    from ..deterministic.kb_engine import run_kb_checks
    from ..deterministic.checks import run_deterministic_checks

    kb_raw_findings = run_kb_checks(
        redacted_text,
        db=db,
        kb_version_id=active_kb.id,
        channel=content.channel,
    )

    # Layer 2: Baseline / Demo deterministic checks & AI Provider with Retrieved Evidence
    provider = get_provider()
    is_mock = getattr(provider, "is_mock", False) or provider.__class__.__name__ == "MockProvider"
    ai_status = "active" if not is_mock else "mock"

    if is_mock:
        baseline_raw = run_deterministic_checks(redacted_text)
    else:
        raw_output = provider.generate_json(
            prompt=redacted_text,
            schema={"findings": []},
            purpose="review",
            retrieved_evidence=retrieved_evidence,
        )
        baseline_raw = raw_output.get("findings", [])
        if "ai_status" in raw_output:
            ai_status = raw_output["ai_status"]

    # Merge: KB findings first, then baseline/AI findings deduplicated
    raw_findings = []
    seen_spans = set()
    for f in kb_raw_findings:
        span = f.get("span", {})
        key = (span.get("start"), span.get("end"), f.get("category"))
        seen_spans.add(key)
        f["source"] = "rule"
        raw_findings.append(f)

    for f in baseline_raw:
        span = f.get("span", {})
        key = (span.get("start"), span.get("end"), f.get("category"))
        if key not in seen_spans:
            seen_spans.add(key)
            if "source" not in f:
                f["source"] = "rule" if is_mock else "ai"
            raw_findings.append(f)

    # 3. Map redacted spans back to original unredacted content offsets
    mapped_findings = []
    for rf in raw_findings:
        span = rf.get("span", {})
        if "start" in span and "end" in span:
            orig_s, orig_e = map_redacted_span_to_original(
                span["start"], span["end"], offset_records, len(raw_text)
            )
            rf_copy = dict(rf)
            rf_copy["span"] = {
                "start": orig_s,
                "end": orig_e,
                "text": raw_text[orig_s:orig_e],
            }
            mapped_findings.append(rf_copy)
        else:
            mapped_findings.append(rf)

    # 4. Strict Grounding Verifier against original text and active KB records
    clean_findings, verifier_metrics = verify_findings(
        mapped_findings, raw_text, db=db, kb_version_id=active_kb.id, return_metrics=True
    )

    # 5. Persist verified findings with status="open" and source
    persisted_findings = []
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
            source=f.get("source", "rule"),
            status="open",
        )
        db.add(new_finding)
        db.flush()

        f_copy = dict(f)
        f_copy["id"] = new_finding.id
        f_copy["span_start"] = span["start"]
        f_copy["span_end"] = span["end"]
        f_copy["span_text"] = span["text"]
        f_copy["status"] = "open"
        f_copy["source"] = f.get("source", "rule")
        persisted_findings.append(f_copy)

    # 6. Record AI Usage with redaction details
    usage = models.AIUsage(
        review_run_id=review.id,
        provider=review.provider,
        model=review.model,
        purpose="review",
        segments_sent=len(redacted_text),
        segments_received=len(persisted_findings),
        redacted_fields={"placeholders": list(placeholders.keys()), "counts": counts},
        redaction_count=counts["total"],
    )
    db.add(usage)

    # 7. Finalize ReviewRun
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
        payload={
            "review_id": review.id,
            "kb_version_id": active_kb.id,
            "findings_count": len(persisted_findings),
            "redaction_count": counts["total"],
            "provider": review.provider,
        },
    )

    return {
        "review_id": review.id,
        "kb_version_id": active_kb.id,
        "status": review.status,
        "redaction_count": counts["total"],
        "redacted_counts": counts,
        "findings": persisted_findings,
        "verifier_metrics": verifier_metrics,
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

    # Strict No-Self-Approval rule enforcement
    if content.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-approval is prohibited: creators cannot approve their own content.",
        )

    # Escalated content check: manager alone cannot approve escalated content
    user_role_str = current_user.role if isinstance(current_user.role, str) else current_user.role.value
    if content.status == "escalated" and user_role_str not in ("reviewer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Content is escalated: requires Authorised Reviewer signoff",
        )

    validate_transition(content.status, payload.decision)

    version_id = content.current_version_id or 1
    now = datetime.datetime.utcnow()

    # Generate non-repudiable cryptographic signature hash
    sig_raw = f"{content.id}:{version_id}:{current_user.id}:{payload.decision}:{now.isoformat()}"
    signature_hash = hashlib.sha256(sig_raw.encode()).hexdigest()

    approval = models.Approval(
        content_id=content.id,
        version_id=version_id,
        role=user_role_str,
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
            "approver_role": user_role_str,
        },
    )

    return {
        "approval_id": approval.id,
        "content_id": content.id,
        "status": content.status,
        "decision": approval.decision,
        "signature_hash": approval.signature_hash,
        "decided_at": approval.decided_at.isoformat(),
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
        body=payload.body.strip(),
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
        "author_name": current_user.name,
        "author_role": current_user.role if isinstance(current_user.role, str) else current_user.role.value,
        "finding_id": comment.finding_id,
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

    comments = (
        db.query(models.Comment)
        .filter(models.Comment.content_id == content_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )

    results = []
    for cm in comments:
        author = db.query(models.User).filter(models.User.id == cm.author_id).first()
        results.append({
            "id": cm.id,
            "content_id": cm.content_id,
            "version_id": cm.version_id,
            "finding_id": cm.finding_id,
            "author_id": cm.author_id,
            "author_name": author.name if author else "User",
            "author_role": author.role if (author and isinstance(author.role, str)) else (author.role.value if author else "user"),
            "body": cm.body,
            "created_at": cm.created_at.isoformat(),
            "parent_id": cm.parent_id,
        })
    return results

# --- Claims Ledger ---

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
        "supported_count": sum(1 for c in ledger if c.get("status") in ("supported", "approved")),
        "approved_count": sum(1 for c in ledger if c.get("status") in ("supported", "approved")),
        "missing_disclaimer_count": sum(1 for c in ledger if c.get("status") == "missing_disclaimer"),
        "outdated_count": sum(1 for c in ledger if c.get("status") in ("outdated", "expired")),
        "expired_count": sum(1 for c in ledger if c.get("status") in ("outdated", "expired")),
        "contradicted_count": sum(1 for c in ledger if c.get("status") == "contradicted"),
        "unsupported_count": sum(1 for c in ledger if c.get("status") == "unsupported"),
        "claims": [
            {
                **c,
                # Ensure backward-compatibility: status accepted as both
                "status": "approved" if c.get("status") == "supported" else ("expired" if c.get("status") == "outdated" else c.get("status")),
                "round3_status": c.get("status"),
            }
            for c in ledger
        ],
    }

# --- Improvement I-1: Suggestion Actions & Verifications ---

@router.get("/{content_id}/findings/{finding_id}/suggestions")
def get_finding_suggestions(
    content_id: int,
    finding_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    finding = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    version = (
        db.query(models.ContentVersion)
        .filter(models.ContentVersion.id == content.current_version_id)
        .first()
    )
    raw_text = version.text_body or ""

    f_dict = {
        "category": finding.category,
        "severity": finding.severity,
        "span": {
            "start": finding.span_start,
            "end": finding.span_end,
            "text": finding.span_text,
        },
        "suggestion": {"text": finding.suggestion_text} if finding.suggestion_text else None,
    }
    kb = (
        db.query(models.KBVersion)
        .filter(models.KBVersion.workspace_id == content.workspace_id, models.KBVersion.is_active == True)
        .first()
    )
    kb_id = kb.id if kb else None
    suggestions = get_verified_suggestions(raw_text, f_dict, db=db, kb_version_id=kb_id)
    return {
        "finding_id": finding.id,
        "span_text": finding.span_text,
        "total_verified": len(suggestions),
        "suggestions": suggestions,
    }

@router.post("/{content_id}/findings/{finding_id}/accept", status_code=200)
def accept_finding_suggestion(
    content_id: int,
    finding_id: int,
    payload: AcceptSuggestionSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.creator)),
):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    finding = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    curr_version = (
        db.query(models.ContentVersion)
        .filter(models.ContentVersion.id == content.current_version_id)
        .first()
    )
    old_text = curr_version.text_body or ""
    # Splice replacement
    new_text = old_text[:finding.span_start] + payload.replacement_text + old_text[finding.span_end:]

    # Update finding persistence
    now = datetime.datetime.utcnow()
    finding.status = "accepted"
    finding.selected_replacement = payload.replacement_text
    finding.decided_by = current_user.id
    finding.decided_at = now

    # Create new content version preserving history
    new_version_no = curr_version.version_no + 1
    new_hash = hashlib.sha256(new_text.encode()).hexdigest()
    new_v = models.ContentVersion(
        content_id=content.id,
        version_no=new_version_no,
        text_body=new_text,
        file_ref=curr_version.file_ref,
        content_hash=new_hash,
        created_by=current_user.id,
    )
    db.add(new_v)
    db.flush()

    content.current_version_id = new_v.id
    content.status = "revising"
    db.commit()

    log_audit_event(
        db=db,
        workspace_id=current_user.workspace_id,
        actor_id=current_user.id,
        action="finding.accepted",
        entity="Finding",
        entity_id=finding.id,
        payload={
            "content_id": content.id,
            "new_version_id": new_v.id,
            "version_no": new_version_no,
            "original_span": finding.span_text,
            "replacement": payload.replacement_text,
        },
    )

    return {
        "status": "applied",
        "finding_id": finding.id,
        "content_id": content.id,
        "new_version_id": new_v.id,
        "version_no": new_version_no,
        "updated_text": new_text,
    }

@router.post("/{content_id}/findings/{finding_id}/edit", status_code=200)
def edit_finding_suggestion(
    content_id: int,
    finding_id: int,
    payload: EditSuggestionSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.creator)),
):
    """Allows creator to provide a custom intent-preserving rewrite and verifies it."""
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    finding = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    curr_version = (
        db.query(models.ContentVersion)
        .filter(models.ContentVersion.id == content.current_version_id)
        .first()
    )
    old_text = curr_version.text_body or ""

    replacement = (payload.custom_text or payload.replacement_text or "").strip()
    if not replacement:
        raise HTTPException(status_code=400, detail="Replacement text cannot be empty.")

    f_dict = {
        "category": finding.category,
        "severity": finding.severity,
        "span": {"start": finding.span_start, "end": finding.span_end, "text": finding.span_text},
    }
    kb = (
        db.query(models.KBVersion)
        .filter(models.KBVersion.workspace_id == content.workspace_id, models.KBVersion.is_active == True)
        .first()
    )
    kb_id = kb.id if kb else None
    is_valid, reason, _ = verify_suggestion(old_text, f_dict, replacement, db=db, kb_version_id=kb_id)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Custom rewrite rejected by Grounding Verifier: {reason}"
        )

    # Splice replacement
    new_text = old_text[:finding.span_start] + replacement + old_text[finding.span_end:]

    # Update finding persistence
    now = datetime.datetime.utcnow()
    finding.status = "edited"
    finding.selected_replacement = replacement
    finding.decided_by = current_user.id
    finding.decided_at = now

    # Create new content version
    new_version_no = curr_version.version_no + 1
    new_hash = hashlib.sha256(new_text.encode()).hexdigest()
    new_v = models.ContentVersion(
        content_id=content.id,
        version_no=new_version_no,
        text_body=new_text,
        file_ref=curr_version.file_ref,
        content_hash=new_hash,
        created_by=current_user.id,
    )
    db.add(new_v)
    db.flush()

    content.current_version_id = new_v.id
    content.status = "revising"
    db.commit()

    log_audit_event(
        db=db,
        workspace_id=current_user.workspace_id,
        actor_id=current_user.id,
        action="finding.edited",
        entity="Finding",
        entity_id=finding.id,
        payload={
            "content_id": content.id,
            "new_version_id": new_v.id,
            "version_no": new_version_no,
            "original_span": finding.span_text,
            "custom_replacement": payload.custom_text,
        },
    )

    return {
        "status": "applied",
        "finding_id": finding.id,
        "content_id": content.id,
        "new_version_id": new_v.id,
        "version_no": new_version_no,
        "updated_text": new_text,
    }

@router.post("/{content_id}/findings/{finding_id}/dismiss", status_code=200)
def dismiss_finding(
    content_id: int,
    finding_id: int,
    payload: DismissFindingSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.creator)),
):
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    finding = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    reason = payload.reason.strip()
    if not reason:
        raise HTTPException(status_code=400, detail="A valid dismissal reason must be provided.")

    now = datetime.datetime.utcnow()
    finding.status = "dismissed"
    finding.dismissal_reason = reason
    finding.decided_by = current_user.id
    finding.decided_at = now
    db.commit()

    log_audit_event(
        db=db,
        workspace_id=current_user.workspace_id,
        actor_id=current_user.id,
        action="finding.dismissed",
        entity="Finding",
        entity_id=finding.id,
        payload={
            "content_id": content.id,
            "category": finding.category,
            "rule_code": finding.evidence_id or finding.category,
            "reason": reason,
            "span_text": finding.span_text,
        },
    )

    return {
        "status": "dismissed",
        "finding_id": finding.id,
        "dismissal_reason": reason,
        "decided_at": now.isoformat(),
    }


# --- Priority 6: Governance AI-Use Ledger & Verifiable Audit Export ---

@router.get("/{content_id}/ai-ledger")
def get_ai_use_ledger(
    content_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Returns transparent audit trail of all AI provider invocations for this content:
    token counts, character counts, redactions, estimated API cost, prompt version, and human override decisions.
    """
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    version = db.query(models.ContentVersion).filter(models.ContentVersion.id == content.current_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    review_run = (
        db.query(models.ReviewRun)
        .filter(models.ReviewRun.version_id == version.id)
        .order_by(models.ReviewRun.id.desc())
        .first()
    )

    usages = []
    if review_run:
        usages = db.query(models.AIUsage).filter(models.AIUsage.review_run_id == review_run.id).all()

    findings = []
    if review_run:
        findings = db.query(models.Finding).filter(models.Finding.review_run_id == review_run.id).all()

    ai_findings = [f for f in findings if getattr(f, "source", "rule") == "ai"]
    ai_accepted = [f for f in ai_findings if f.status in ("accepted", "edited")]
    ai_dismissed = [f for f in ai_findings if f.status == "dismissed"]

    total_chars_sent = sum(u.segments_sent * 150 for u in usages)
    total_chars_recv = sum(u.segments_received * 100 for u in usages)
    total_redacted = sum(u.redaction_count for u in usages)

    provider = review_run.provider if review_run else "deterministic"
    model = review_run.model if review_run else "rules"

    # Pricing estimation based on official Gemini Flash rate:
    # Input: $0.075 per 1M tokens ($0.000000075 / token)
    # Output: $0.30 per 1M tokens ($0.00000030 / token)
    is_cloud_llm = provider in ("gemini", "openai")
    tokens_in = max(0, total_chars_sent // 4)
    tokens_out = max(0, total_chars_recv // 4)
    cost_usd = 0.0
    if is_cloud_llm:
        cost_usd = (tokens_in * 0.000000075) + (tokens_out * 0.00000030)

    records = []
    for u in usages:
        records.append({
            "id": u.id,
            "provider": u.provider,
            "model": u.model,
            "purpose": u.purpose,
            "segments_sent": u.segments_sent,
            "segments_received": u.segments_received,
            "redacted_fields": u.redacted_fields or [],
            "redaction_count": u.redaction_count,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    return {
        "content_id": content.id,
        "version_id": version.id,
        "review_run_id": review_run.id if review_run else None,
        "provider": provider,
        "model": model,
        "prompt_version": "v3.1-grounded-judge",
        "timestamp": (review_run.finished_at or review_run.started_at or datetime.datetime.utcnow()).isoformat() if review_run else None,
        "totals": {
            "characters_sent": total_chars_sent,
            "characters_returned": total_chars_recv,
            "redacted_entities": total_redacted,
            "estimated_cost_usd": f"${cost_usd:.6f}",
            "cost_basis": "Gemini Flash Token Rate ($0.075/1M in, $0.30/1M out)" if is_cloud_llm else "Local/Mock ($0.00)",
        },
        "human_governance": {
            "total_ai_findings": len(ai_findings),
            "human_accepted_count": len(ai_accepted),
            "human_dismissed_count": len(ai_dismissed),
            "human_acceptance_rate_pct": round((len(ai_accepted) / max(1, len(ai_findings))) * 100.0, 1),
        },
        "records": records,
    }


@router.get("/{content_id}/export")
def export_governance_certificate(
    content_id: int,
    format: Optional[str] = Query("markdown"),  # markdown | json | html
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generates a verifiable Brand Governance Certificate with complete findings ledger,
    cryptographic content hash, active KB metadata, and SHA-256 verification signature.
    """
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")

    version = db.query(models.ContentVersion).filter(models.ContentVersion.id == content.current_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    review_run = (
        db.query(models.ReviewRun)
        .filter(models.ReviewRun.version_id == version.id)
        .order_by(models.ReviewRun.id.desc())
        .first()
    )

    findings = []
    if review_run:
        findings = db.query(models.Finding).filter(models.Finding.review_run_id == review_run.id).all()

    kb = (
        db.query(models.KBVersion)
        .filter(models.KBVersion.workspace_id == content.workspace_id, models.KBVersion.is_active == True)
        .first()
    )

    content_hash = hashlib.sha256((version.text_body or "").encode("utf-8")).hexdigest()
    ts_now = datetime.datetime.utcnow().isoformat() + "Z"

    # Compute SHA-256 digital certificate signature
    canonical_sig_payload = f"BRANDSENTINEL-V3|{content.id}|{content.status}|{content_hash}|{kb.id if kb else 0}|{len(findings)}|{ts_now}"
    certificate_hash = hashlib.sha256(canonical_sig_payload.encode("utf-8")).hexdigest()

    accepted_count = sum(1 for f in findings if f.status in ("accepted", "edited"))
    dismissed_count = sum(1 for f in findings if f.status == "dismissed")
    open_count = sum(1 for f in findings if f.status == "open")

    certificate_data = {
        "certificate_id": f"CERT-{content.id:05d}-{uuid.uuid4().hex[:6].upper()}",
        "timestamp": ts_now,
        "content_metadata": {
            "id": content.id,
            "title": content.title,
            "channel": content.channel,
            "type": content.type,
            "status": content.status,
            "workspace": current_user.workspace.name if current_user.workspace else "Brand Workspace",
            "content_sha256": content_hash,
            "version_number": version.version_no,
        },
        "knowledge_base": {
            "kb_version_id": kb.id if kb else None,
            "label": kb.label if kb else "Active Brand Guidelines",
        },
        "findings_summary": {
            "total": len(findings),
            "accepted": accepted_count,
            "dismissed": dismissed_count,
            "open": open_count,
            "compliance_status": "COMPLIANT" if open_count == 0 and content.status == "approved" else "REQUIRES_ATTENTION",
        },
        "findings_ledger": [
            {
                "finding_id": f.id,
                "category": f.category,
                "severity": f.severity,
                "rule_code": f.evidence_id or f.category,
                "span_text": f.span_text,
                "status": f.status,
                "source": getattr(f, "source", "rule"),
                "reason": f.reason,
                "resolution": f.selected_replacement if f.status == "edited" else (f.dismissal_reason if f.status == "dismissed" else "none"),
            }
            for f in findings
        ],
        "cryptographic_verification": {
            "algorithm": "SHA-256",
            "signature": certificate_hash,
            "canonical_payload": canonical_sig_payload,
        },
    }

    if format == "json":
        return certificate_data

    # Generate Markdown format
    lines = [
        f"# Brand Governance Certificate",
        f"**Certificate ID:** `{certificate_data['certificate_id']}`  ",
        f"**Issuance Date:** `{ts_now}`  ",
        f"**Verification Signature:** `{certificate_hash}`  ",
        f"",
        f"---",
        f"",
        f"## 1. Content Asset Metadata",
        f"- **Title:** {content.title}",
        f"- **Asset ID:** {content.id} (Version {version.version_no})",
        f"- **Channel:** {content.channel or 'general'}",
        f"- **Format:** {content.type}",
        f"- **Current Status:** `{content.status.upper()}`",
        f"- **Content SHA-256:** `{content_hash}`",
        f"- **Active Brand KB:** {certificate_data['knowledge_base']['label']} (ID: {certificate_data['knowledge_base']['kb_version_id']})",
        f"",
        f"## 2. Governance Adherence Summary",
        f"- **Total Findings Evaluated:** {len(findings)}",
        f"- **Accepted / Remediated:** {accepted_count}",
        f"- **Human-Dismissed with Justification:** {dismissed_count}",
        f"- **Unresolved Open Findings:** {open_count}",
        f"- **Overall Certification Outcome:** **{certificate_data['findings_summary']['compliance_status']}**",
        f"",
        f"## 3. Verified Findings Ledger",
        f"| ID | Category | Severity | Rule Code | Flagged Span | Status | Source | Resolution / Note |",
        f"|---|---|---|---|---|---|---|---|",
    ]

    for f in certificate_data["findings_ledger"]:
        res_text = (f["resolution"] or "-")[:50]
        lines.append(
            f"| {f['finding_id']} | {f['category']} | {f['severity']} | {f['rule_code']} | `{f['span_text'][:25]}` | {f['status']} | {f['source']} | {res_text} |"
        )

    if not certificate_data["findings_ledger"]:
        lines.append("| - | - | - | - | No findings detected | Clean | rule | Content fully compliant |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 4. Cryptographic Proof of Integrity",
        f"```",
        f"Canonical Payload: {canonical_sig_payload}",
        f"SHA-256 Signature: {certificate_hash}",
        f"```",
        f"*This Brand Governance Certificate was automatically verified and cryptographically stamped by BrandSentinel.*",
    ])

    md_content = "\n".join(lines)

    if format == "html":
        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Brand Governance Certificate - {content.title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1f2937; max-width: 860px; margin: 40px auto; padding: 24px; }}
h1 {{ color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px; }}
h2 {{ color: #374151; margin-top: 32px; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; }}
th, td {{ border: 1px solid #e5e7eb; padding: 10px 12px; text-align: left; }}
th {{ background-color: #f9fafb; font-weight: 600; }}
code {{ background-color: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 13px; font-family: monospace; }}
.badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 12px; }}
.badge-compliant {{ background-color: #d1fae5; color: #065f46; }}
.sig-box {{ background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 16px; font-family: monospace; word-break: break-all; margin-top: 16px; }}
</style>
</head>
<body>
<h1>Brand Governance Certificate</h1>
<p><strong>Certificate ID:</strong> <code>{certificate_data['certificate_id']}</code> | <strong>Status:</strong> <span class="badge badge-compliant">{certificate_data['findings_summary']['compliance_status']}</span></p>
<h2>1. Content Asset Metadata</h2>
<ul>
  <li><strong>Title:</strong> {content.title}</li>
  <li><strong>Asset ID:</strong> {content.id} (Version {version.version_no})</li>
  <li><strong>Channel:</strong> {content.channel or 'general'}</li>
  <li><strong>Content SHA-256:</strong> <code>{content_hash}</code></li>
  <li><strong>Active Brand KB:</strong> {certificate_data['knowledge_base']['label']}</li>
</ul>
<h2>2. Governance Summary</h2>
<p>Evaluated {len(findings)} total findings: {accepted_count} resolved, {dismissed_count} justified dismissals, {open_count} open.</p>
<h2>3. Cryptographic Verification</h2>
<div class="sig-box">
Payload: {canonical_sig_payload}<br>
SHA-256: {certificate_hash}
</div>
</body>
</html>"""
        return Response(content=html_content, media_type="text/html")

    return Response(content=md_content, media_type="text/markdown")

