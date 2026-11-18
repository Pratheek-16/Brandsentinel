import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...db import session, models
from ...core.security import get_current_user

router = APIRouter(prefix="/insights", tags=["insights"])

@router.get("/summary")
def get_insights_summary(
    channel: Optional[str] = None,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    ws_id = current_user.workspace_id

    content_query = db.query(models.Content).filter(models.Content.workspace_id == ws_id)
    if channel:
        content_query = content_query.filter(models.Content.channel == channel)

    total_contents = content_query.count()
    approved_contents = content_query.filter(models.Content.status == "approved").count()
    rejected_contents = content_query.filter(models.Content.status == "rejected").count()
    in_review_contents = content_query.filter(models.Content.status.in_(["submitted", "manager_review", "escalated"])).count()
    revising_contents = content_query.filter(models.Content.status.in_(["draft", "revising", "changes_requested"])).count()

    # Findings aggregation by category
    cat_query = (
        db.query(models.Finding.category, func.count(models.Finding.id))
        .join(models.ReviewRun, models.Finding.review_run_id == models.ReviewRun.id)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .join(models.Content, models.ContentVersion.content_id == models.Content.id)
        .filter(models.Content.workspace_id == ws_id)
    )
    if channel:
        cat_query = cat_query.filter(models.Content.channel == channel)
    findings_by_category = {cat: count for cat, count in cat_query.group_by(models.Finding.category).all()}

    # Findings aggregation by severity
    sev_query = (
        db.query(models.Finding.severity, func.count(models.Finding.id))
        .join(models.ReviewRun, models.Finding.review_run_id == models.ReviewRun.id)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .join(models.Content, models.ContentVersion.content_id == models.Content.id)
        .filter(models.Content.workspace_id == ws_id)
    )
    if channel:
        sev_query = sev_query.filter(models.Content.channel == channel)
    findings_by_severity = {sev: count for sev, count in sev_query.group_by(models.Finding.severity).all()}

    # Finding status breakdown (open, accepted, edited, dismissed)
    status_query = (
        db.query(models.Finding.status, func.count(models.Finding.id))
        .join(models.ReviewRun, models.Finding.review_run_id == models.ReviewRun.id)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .join(models.Content, models.ContentVersion.content_id == models.Content.id)
        .filter(models.Content.workspace_id == ws_id)
    )
    if channel:
        status_query = status_query.filter(models.Content.channel == channel)
    findings_by_status = {st: count for st, count in status_query.group_by(models.Finding.status).all()}

    # Redactions total
    redactions_total = (
        db.query(func.sum(models.AIUsage.redaction_count))
        .join(models.ReviewRun, models.AIUsage.review_run_id == models.ReviewRun.id)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .join(models.Content, models.ContentVersion.content_id == models.Content.id)
        .filter(models.Content.workspace_id == ws_id)
        .scalar()
    ) or 0

    # Content by channel distribution
    channel_query = (
        db.query(models.Content.channel, func.count(models.Content.id))
        .filter(models.Content.workspace_id == ws_id)
        .group_by(models.Content.channel)
        .all()
    )
    contents_by_channel = {ch or "unassigned": count for ch, count in channel_query}

    # Stale facts count
    kb = db.query(models.KBVersion).filter(models.KBVersion.workspace_id == ws_id, models.KBVersion.is_active == True).first()
    now = datetime.datetime.utcnow()
    stale_facts_count = 0
    if kb:
        stale_facts_count = db.query(models.Fact).filter(models.Fact.kb_version_id == kb.id, models.Fact.valid_to < now).count()

    total_findings_count = sum(findings_by_category.values())
    acceptance_rate = 0.0
    total_resolved = findings_by_status.get("accepted", 0) + findings_by_status.get("dismissed", 0) + findings_by_status.get("edited", 0)
    if total_resolved > 0:
        acceptance_rate = round((findings_by_status.get("accepted", 0) + findings_by_status.get("edited", 0)) / total_resolved * 100.0, 1)

    return {
        "workspace_id": ws_id,
        "content_counts": {
            "total": total_contents,
            "approved": approved_contents,
            "rejected": rejected_contents,
            "in_review": in_review_contents,
            "revising": revising_contents,
        },
        "total_findings": total_findings_count,
        "acceptance_rate_pct": acceptance_rate,
        "findings_by_category": findings_by_category,
        "findings_by_severity": findings_by_severity,
        "findings_by_status": findings_by_status,
        "contents_by_channel": contents_by_channel,
        "total_pii_redacted": redactions_total,
        "stale_facts_count": stale_facts_count,
    }

@router.get("/ambiguity")
def get_ambiguity_analysis(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Calculates real dismissal and override rates by rule across workspace content.
    Identifies rules with >= 40% creator dismissal rate as ambiguous.
    Also detects stale facts and provides honest status states.
    """
    ws_id = current_user.workspace_id

    # Join findings through ReviewRun and ContentVersion to current workspace
    findings = (
        db.query(models.Finding)
        .join(models.ReviewRun, models.Finding.review_run_id == models.ReviewRun.id)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .join(models.Content, models.ContentVersion.content_id == models.Content.id)
        .filter(models.Content.workspace_id == ws_id)
        .all()
    )

    # Group by evidence_id (the rule/fact code)
    rule_stats: Dict[str, Dict[str, Any]] = {}
    for f in findings:
        code = f.evidence_id or f.category
        if code not in rule_stats:
            rule_stats[code] = {
                "rule_code": code,
                "category": f.category,
                "total_surfaced": 0,
                "accepted_count": 0,
                "dismissed_count": 0,
                "open_count": 0,
                "reasons": [],
            }
        rule_stats[code]["total_surfaced"] += 1
        if f.status == "accepted" or f.status == "edited":
            rule_stats[code]["accepted_count"] += 1
        elif f.status == "dismissed":
            rule_stats[code]["dismissed_count"] += 1
            if f.dismissal_reason:
                rule_stats[code]["reasons"].append(f.dismissal_reason)
        else:
            rule_stats[code]["open_count"] += 1

    flagged_rules = []
    monitored_rules = []

    for code, stats in rule_stats.items():
        surfaced = stats["total_surfaced"]
        dismissed = stats["dismissed_count"]
        dismissal_rate = round((dismissed / max(1, surfaced)) * 100.0, 1)

        rule_data = {
            "rule_code": code,
            "category": stats["category"],
            "total_surfaced": surfaced,
            "dismissed_count": dismissed,
            "accepted_count": stats["accepted_count"],
            "dismissal_rate_pct": dismissal_rate,
            "sample_dismissal_reasons": stats["reasons"][:3],
        }

        # Threshold: if surfaced >= 2 and dismissal_rate >= 40%, flag as ambiguous
        if surfaced >= 2 and dismissal_rate >= 40.0:
            rule_data["status"] = "flagged_ambiguous"
            rule_data["recommendation"] = (
                f"Rule '{code}' shows high creator dismissals ({dismissal_rate}% of {surfaced} instances). "
                "Consider refining guideline wording, adding positive/negative examples, or clarifying exceptions."
            )
            flagged_rules.append(rule_data)
        else:
            rule_data["status"] = "normal"
            rule_data["recommendation"] = "Operating within normal acceptance thresholds."
            monitored_rules.append(rule_data)

    # If no rules flagged yet, provide healthy baseline status
    if not flagged_rules:
        flagged_rules.append({
            "rule_code": "R-GOVERNANCE-BASELINE",
            "category": "tone",
            "total_surfaced": 0,
            "dismissed_count": 0,
            "accepted_count": 0,
            "dismissal_rate_pct": 0.0,
            "status": "monitored",
            "recommendation": "All active rules operating within normal acceptance thresholds (< 40% dismissals).",
            "sample_dismissal_reasons": [],
        })

    # Detect stale facts in active KB
    kb = db.query(models.KBVersion).filter(models.KBVersion.workspace_id == ws_id, models.KBVersion.is_active == True).first()
    now = datetime.datetime.utcnow()
    stale_facts = []
    if kb:
        stale_records = db.query(models.Fact).filter(models.Fact.kb_version_id == kb.id, models.Fact.valid_to < now).all()
        for sf in stale_records:
            stale_facts.append({
                "code": sf.code,
                "key": sf.key,
                "value": sf.value,
                "valid_to": sf.valid_to.isoformat() if sf.valid_to else None,
                "warning": f"Fact '{sf.key}' expired on {sf.valid_to.strftime('%Y-%m-%d') if sf.valid_to else 'unknown'}. Update or retire value.",
            })

    total_evaluated = len(rule_stats)
    health_status = "needs_attention" if (len(flagged_rules) > 1 or stale_facts) else "healthy"

    return {
        "workspace_id": ws_id,
        "health_status": health_status,
        "total_rules_evaluated": total_evaluated,
        "ambiguous_rules_count": len([r for r in flagged_rules if r["status"] == "flagged_ambiguous"]),
        "flagged_rules": flagged_rules,
        "flagged_ambiguous_rules": [r for r in flagged_rules if r["status"] == "flagged_ambiguous"],
        "monitored_rules": monitored_rules,
        "stale_facts": stale_facts,
    }
