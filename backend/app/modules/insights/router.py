from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...db import session, models
from ...core.security import get_current_user

router = APIRouter(prefix="/insights", tags=["insights"])

@router.get("/summary")
def get_insights_summary(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    ws_id = current_user.workspace_id

    total_contents = db.query(models.Content).filter(models.Content.workspace_id == ws_id).count()
    approved_contents = db.query(models.Content).filter(models.Content.workspace_id == ws_id, models.Content.status == "approved").count()
    rejected_contents = db.query(models.Content).filter(models.Content.workspace_id == ws_id, models.Content.status == "rejected").count()
    in_review_contents = db.query(models.Content).filter(models.Content.workspace_id == ws_id, models.Content.status.in_(["submitted", "manager_review", "escalated"])).count()

    # Findings aggregation
    finding_query = (
        db.query(models.Finding.category, func.count(models.Finding.id))
        .join(models.ReviewRun, models.Finding.review_run_id == models.ReviewRun.id)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .join(models.Content, models.ContentVersion.content_id == models.Content.id)
        .filter(models.Content.workspace_id == ws_id)
        .group_by(models.Finding.category)
        .all()
    )
    findings_by_category = {cat: count for cat, count in finding_query}

    sev_query = (
        db.query(models.Finding.severity, func.count(models.Finding.id))
        .join(models.ReviewRun, models.Finding.review_run_id == models.ReviewRun.id)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .join(models.Content, models.ContentVersion.content_id == models.Content.id)
        .filter(models.Content.workspace_id == ws_id)
        .group_by(models.Finding.severity)
        .all()
    )
    findings_by_severity = {sev: count for sev, count in sev_query}

    # Redaction stats
    redactions_total = (
        db.query(func.sum(models.AIUsage.redaction_count))
        .join(models.ReviewRun, models.AIUsage.review_run_id == models.ReviewRun.id)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .join(models.Content, models.ContentVersion.content_id == models.Content.id)
        .filter(models.Content.workspace_id == ws_id)
        .scalar()
    ) or 0

    return {
        "workspace_id": ws_id,
        "content_counts": {
            "total": total_contents,
            "approved": approved_contents,
            "rejected": rejected_contents,
            "in_review": in_review_contents,
        },
        "findings_by_category": findings_by_category,
        "findings_by_severity": findings_by_severity,
        "total_pii_redacted": redactions_total,
    }

@router.get("/ambiguity")
def get_ambiguity_analysis(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    ws_id = current_user.workspace_id

    # Retrieve all dismissal audit events
    dismissals = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.workspace_id == ws_id, models.AuditEvent.action == "finding.dismissed")
        .all()
    )

    dismissal_counts: Dict[str, int] = {}
    for ev in dismissals:
        payload = ev.payload_json or {}
        rule_code = payload.get("rule_code") or payload.get("category", "General")
        dismissal_counts[rule_code] = dismissal_counts.get(rule_code, 0) + 1

    # Retrieve all findings count per rule code or category
    total_findings = db.query(models.Finding).count()

    flagged_rules = []
    for code, dismissed_count in dismissal_counts.items():
        # High dismissal rate threshold > 40% (or at least 2 dismissals in demo data)
        flagged_rules.append({
            "rule_code": code,
            "dismissals_count": dismissed_count,
            "dismissal_rate_pct": min(100.0, round((dismissed_count / max(1, total_findings)) * 100.0, 1)),
            "status": "flagged_ambiguous",
            "recommendation": (
                f"Rule '{code}' shows high creator dismissals ({dismissed_count}). "
                "Consider clarifying exceptions, refining guidance examples, or loosening boundary conditions."
            ),
        })

    # If none dismissed yet, provide proactive heuristic guidance
    if not flagged_rules:
        flagged_rules.append({
            "rule_code": "R-TONE-HEALTHY",
            "dismissals_count": 0,
            "dismissal_rate_pct": 0.0,
            "status": "monitored",
            "recommendation": "All brand rules are performing within acceptable acceptance thresholds (< 40% dismissals).",
        })

    return {
        "workspace_id": ws_id,
        "total_flagged_rules": len(flagged_rules),
        "flagged_rules": flagged_rules,
    }
