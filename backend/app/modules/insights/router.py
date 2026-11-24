import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...db import session, models
from ...core.security import get_current_user, require_roles
from ...core.datetime_utils import utc_now
from ...modules.audit.chain import log_audit_event

router = APIRouter(prefix="/insights", tags=["insights"])


class AcceptClarificationRequest(BaseModel):
    signal_type: str  # "high_dismissal", "conflicting_term", "conflicting_fact", "stale_fact", "conflicting_rule", "ai_human_disagreement"
    target_code: Optional[str] = None  # rule code or fact code
    term_preferred: Optional[str] = None  # if updating term
    clarified_text: str
    new_valid_to: Optional[datetime.datetime] = None
    new_value: Optional[str] = None


def generate_clarification_proposal(signal_type: str, item: Dict[str, Any]) -> str:
    """Generate deterministic, concrete guideline clarification rewording."""
    if signal_type == "high_dismissal":
        code = item.get("rule_code", "RULE")
        cat = item.get("category", "guideline")
        return (
            f"Clarify scope for rule '{code}': Restrict enforcement to external consumer-facing marketing materials, "
            f"and add explicit exemption for technical documentation and verified customer case studies."
        )
    elif signal_type == "conflicting_term":
        term = item.get("term", "term")
        pref = item.get("preferred", "preferred_term")
        return (
            f"Resolve terminology conflict: Confirm '{pref}' as the single official brand standard; "
            f"remove '{term}' from prohibited variants list and update associated style guidelines."
        )
    elif signal_type == "conflicting_fact":
        key = item.get("key", "attribute")
        val1 = item.get("value_1", "v1")
        val2 = item.get("value_2", "v2")
        return (
            f"Establish single source of truth for fact '{key}': Retire older value '{val1}' with past valid_to date, "
            f"and authorize current value '{val2}' as active specification."
        )
    elif signal_type == "stale_fact":
        key = item.get("key", "fact")
        val = item.get("value", "")
        return (
            f"Revalidate fact '{key}' (current value: '{val}'): Conduct product team review, update specification if changed, "
            f"and extend valid_to date to 12 months from today."
        )
    elif signal_type == "ai_human_disagreement":
        code = item.get("rule_code", "RULE")
        return (
            f"Refine AI review boundary for rule '{code}': Add explicit negative examples and bounding context "
            f"so automated models do not flag permissible contextual variations."
        )
    elif signal_type == "unused_rule":
        code = item.get("code", "RULE")
        return (
            f"Review rule '{code}' relevance: Determine whether rule is obsolete or requires broader enforcement criteria."
        )
    return "Clarify guideline wording to eliminate operational ambiguity."
    return f"Update policy wording to resolve ambiguity in '{item.get('rule_code', 'rule')}'."


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

    redactions_total = (
        db.query(func.sum(models.AIUsage.redaction_count))
        .join(models.ReviewRun, models.AIUsage.review_run_id == models.ReviewRun.id)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .join(models.Content, models.ContentVersion.content_id == models.Content.id)
        .filter(models.Content.workspace_id == ws_id)
        .scalar()
    ) or 0

    channel_query = (
        db.query(models.Content.channel, func.count(models.Content.id))
        .filter(models.Content.workspace_id == ws_id)
        .group_by(models.Content.channel)
        .all()
    )
    contents_by_channel = {ch or "unassigned": count for ch, count in channel_query}

    kb = db.query(models.KBVersion).filter(models.KBVersion.workspace_id == ws_id, models.KBVersion.is_active == True).first()
    now = utc_now()
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
    """Calculates comprehensive governance ambiguity across 4 real signals:
    1. Rules with high human dismissal/override rate (> 40% with sample size >= 3)
    2. Conflicting rules, terms, and facts within active KB
    3. Stale facts (expired valid_to or unreviewed)
    4. AI-vs-human disagreement signals
    """
    ws_id = current_user.workspace_id
    now = utc_now()

    # Active KB
    kb = db.query(models.KBVersion).filter(models.KBVersion.workspace_id == ws_id, models.KBVersion.is_active == True).first()

    # 1. Human dismissal analysis
    findings = (
        db.query(models.Finding)
        .join(models.ReviewRun, models.Finding.review_run_id == models.ReviewRun.id)
        .join(models.ContentVersion, models.ReviewRun.version_id == models.ContentVersion.id)
        .join(models.Content, models.ContentVersion.content_id == models.Content.id)
        .filter(models.Content.workspace_id == ws_id)
        .all()
    )

    rule_stats: Dict[str, Dict[str, Any]] = {}
    ai_disagreements = []

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
        if f.status in ["accepted", "edited"]:
            rule_stats[code]["accepted_count"] += 1
        elif f.status == "dismissed":
            rule_stats[code]["dismissed_count"] += 1
            if f.dismissal_reason:
                rule_stats[code]["reasons"].append(f.dismissal_reason)
        else:
            rule_stats[code]["open_count"] += 1

        # Check for AI-vs-human disagreement
        if getattr(f, "source", "rule") == "ai" and f.status == "dismissed":
            reason_text = (f.dismissal_reason or "").lower()
            if any(term in reason_text for term in ["false positive", "hallucination", "allowed", "context", "permissible", "ok"]):
                ai_disagreements.append({
                    "finding_id": f.id,
                    "rule_code": code,
                    "span_text": f.span_text,
                    "reason": f.dismissal_reason,
                    "explanation": f"Human reviewer dismissed AI finding on '{f.span_text}' citing '{f.dismissal_reason}'.",
                })

    flagged_rules = []
    monitored_rules = []

    for code, stats in rule_stats.items():
        surfaced = stats["total_surfaced"]
        dismissed = stats["dismissed_count"]
        dismissal_rate = round((dismissed / max(1, surfaced)) * 100.0, 1)

        rule_data = {
            "signal_type": "high_dismissal",
            "rule_code": code,
            "category": stats["category"],
            "total_surfaced": surfaced,
            "dismissed_count": dismissed,
            "accepted_count": stats["accepted_count"],
            "dismissal_rate_pct": dismissal_rate,
            "sample_dismissal_reasons": stats["reasons"][:3],
        }

        # Threshold: sample size >= 3 and dismissal rate > 40.0% OR 100% dismissal with surfaced >= 1
        if (surfaced >= 3 and dismissal_rate > 40.0) or (surfaced >= 1 and dismissed == surfaced):
            rule_data["status"] = "flagged_ambiguous"
            rule_data["recommendation"] = (
                f"Rule '{code}' shows high creator dismissals ({dismissal_rate}% across {surfaced} instances). "
                "Guideline boundaries appear ambiguous to content creators."
            )
            rule_data["suggested_clarification"] = generate_clarification_proposal("high_dismissal", rule_data)
            flagged_rules.append(rule_data)
        else:
            rule_data["status"] = "normal"
            rule_data["recommendation"] = "Operating within acceptable adherence thresholds."
            monitored_rules.append(rule_data)

    # 2. Conflicting rules and terms in active KB
    conflicting_items = []
    if kb:
        # (a) Conflicting terms: term in banned list that is also preferred, or vice-versa
        terms = db.query(models.Term).filter(models.Term.kb_version_id == kb.id).all()
        preferred_set = {t.preferred.strip().lower(): t.preferred for t in terms}
        for t in terms:
            banned_variants = t.banned if isinstance(t.banned, list) else []
            for b in banned_variants:
                if not isinstance(b, str):
                    continue
                b_clean = b.strip().lower()
                if b_clean in preferred_set and b_clean != t.preferred.strip().lower():
                    pref_match = preferred_set[b_clean]
                    c_data = {
                        "signal_type": "conflicting_term",
                        "term": b,
                        "preferred": pref_match,
                        "description": f"Term '{b}' is marked banned in one entry but preferred as '{pref_match}' in another.",
                    }
                    c_data["suggested_clarification"] = generate_clarification_proposal("conflicting_term", c_data)
                    conflicting_items.append(c_data)

        # (b) Conflicting facts: same key with overlapping validity dates and conflicting values
        facts = db.query(models.Fact).filter(models.Fact.kb_version_id == kb.id).all()
        for i in range(len(facts)):
            for j in range(i + 1, len(facts)):
                f1 = facts[i]
                f2 = facts[j]
                if f1.key.strip().lower() == f2.key.strip().lower() and (f1.value != f2.value or f1.unit != f2.unit):
                    # Check validity overlap
                    f1_from = f1.valid_from or datetime.datetime.min
                    f1_to = f1.valid_to or datetime.datetime.max
                    f2_from = f2.valid_from or datetime.datetime.min
                    f2_to = f2.valid_to or datetime.datetime.max

                    if f1_from <= f2_to and f2_from <= f1_to:
                        c_fact = {
                            "signal_type": "conflicting_fact",
                            "key": f1.key,
                            "fact_1_code": f1.code,
                            "value_1": f"{f1.value} {f1.unit or ''}".strip(),
                            "fact_2_code": f2.code,
                            "value_2": f"{f2.value} {f2.unit or ''}".strip(),
                            "description": f"Conflicting values for fact '{f1.key}': '{f1.value}' ({f1.code}) vs '{f2.value}' ({f2.code}) with overlapping dates.",
                        }
                        c_fact["suggested_clarification"] = generate_clarification_proposal("conflicting_fact", c_fact)
                        conflicting_items.append(c_fact)

        # (c) Conflicting rules: contradictory severity or rules in same category
        rules = db.query(models.Rule).filter(models.Rule.kb_version_id == kb.id).all()
        for i in range(len(rules)):
            for j in range(i + 1, len(rules)):
                r1 = rules[i]
                r2 = rules[j]
                if r1.category == r2.category and r1.code != r2.code:
                    # Check for contradictory severity e.g. blocker vs minor on same topic
                    if (r1.severity_default == "blocker" and r2.severity_default == "minor") and (
                        any(w in r2.text.lower() for w in r1.text.lower().split() if len(w) > 5)
                    ):
                        c_rule = {
                            "signal_type": "conflicting_rule",
                            "category": r1.category,
                            "rule_1_code": r1.code,
                            "rule_2_code": r2.code,
                            "description": f"Conflicting severity across related rules '{r1.code}' ({r1.severity_default}) and '{r2.code}' ({r2.severity_default}).",
                        }
                        c_rule["suggested_clarification"] = generate_clarification_proposal("conflicting_rule", c_rule)
                        conflicting_items.append(c_rule)

    # 3. Stale facts in active KB
    stale_facts = []
    if kb:
        stale_records = db.query(models.Fact).filter(models.Fact.kb_version_id == kb.id).all()
        for sf in stale_records:
            is_expired = sf.valid_to and sf.valid_to < now
            is_aged = (not sf.valid_to) and (sf.valid_from and (now - sf.valid_from).days > 180)
            if is_expired or is_aged:
                sf_info = {
                    "signal_type": "stale_fact",
                    "code": sf.code,
                    "key": sf.key,
                    "value": sf.value,
                    "unit": sf.unit,
                    "valid_to": sf.valid_to.isoformat() if sf.valid_to else None,
                    "warning": f"Fact '{sf.key}' expired on {sf.valid_to.strftime('%Y-%m-%d') if sf.valid_to else 'unknown'}. Update or retire value.",
                }
                sf_info["suggested_clarification"] = generate_clarification_proposal("stale_fact", sf_info)
                stale_facts.append(sf_info)

    # 4. AI-vs-human disagreement summary
    ai_disagreement_signals = []
    for ad in ai_disagreements:
        signal = {
            "signal_type": "ai_human_disagreement",
            "rule_code": ad["rule_code"],
            "finding_id": ad["finding_id"],
            "span_text": ad["span_text"],
            "human_dismissal_reason": ad["reason"],
            "description": ad["explanation"],
        }
        signal["suggested_clarification"] = generate_clarification_proposal("ai_human_disagreement", signal)
        ai_disagreement_signals.append(signal)

    # 5. Unused rules in active KB
    unused_rules = []
    if kb:
        active_rules = db.query(models.Rule).filter(models.Rule.kb_version_id == kb.id).all()
        for r in active_rules:
            if r.code not in rule_stats and r.category not in rule_stats:
                u_item = {
                    "signal_type": "unused_rule",
                    "code": r.code,
                    "category": r.category,
                    "text": r.text,
                    "description": f"Rule '{r.code}' has never been triggered across any content reviews.",
                }
                u_item["suggested_clarification"] = generate_clarification_proposal("unused_rule", u_item)
                unused_rules.append(u_item)

    # Compile all signals
    all_signals = []
    all_signals.extend(flagged_rules)
    all_signals.extend(conflicting_items)
    all_signals.extend(stale_facts)
    all_signals.extend(ai_disagreement_signals)
    all_signals.extend(unused_rules)

    health_status = "healthy"
    if len(flagged_rules) > 0 or len(conflicting_items) > 0 or len(stale_facts) > 0:
        health_status = "needs_attention"
    if len(conflicting_items) > 1 or len(stale_facts) > 2:
        health_status = "critical"

    return {
        "workspace_id": ws_id,
        "health_status": health_status,
        "total_rules_evaluated": len(rule_stats),
        "total_ambiguity_signals": len(all_signals),
        "breakdown": {
            "high_dismissal_count": len(flagged_rules),
            "conflicting_items_count": len(conflicting_items),
            "stale_facts_count": len(stale_facts),
            "ai_disagreements_count": len(ai_disagreement_signals),
            "unused_rules_count": len(unused_rules),
        },
        "all_signals": all_signals,
        "flagged_rules": flagged_rules,
        "flagged_ambiguous_rules": flagged_rules,
        "conflicting_items": conflicting_items,
        "stale_facts": stale_facts,
        "ai_disagreements": ai_disagreement_signals,
        "unused_rules": unused_rules,
        "monitored_rules": monitored_rules,
    }


@router.post("/accept-clarification")
def accept_clarification(
    payload: AcceptClarificationRequest,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin, models.RoleEnum.reviewer)),
):
    """Accept an ambiguity clarification by creating a NEW active KB version with the updated policy."""
    ws_id = current_user.workspace_id

    current_kb = (
        db.query(models.KBVersion)
        .filter(models.KBVersion.workspace_id == ws_id, models.KBVersion.is_active == True)
        .first()
    )
    if not current_kb:
        raise HTTPException(status_code=404, detail="No active KB version found in current workspace.")

    # Deactivate all existing versions in this workspace
    db.query(models.KBVersion).filter(models.KBVersion.workspace_id == ws_id).update({"is_active": False})
    db.flush()

    # Create new snapshot version
    label_suffix = payload.target_code or payload.term_preferred or payload.signal_type
    new_label = f"Guidelines vNext ({label_suffix}) - {utc_now().strftime('%Y-%m-%d %H:%M')}"
    new_kb = models.KBVersion(
        workspace_id=ws_id,
        label=new_label,
        created_by=current_user.id,
        is_active=True,
    )
    db.add(new_kb)
    db.flush()

    # 1. Clone Rules and apply clarification if targeted
    rules = db.query(models.Rule).filter(models.Rule.kb_version_id == current_kb.id).all()
    updated_rule = None
    for r in rules:
        rule_text = r.text
        if payload.target_code and r.code == payload.target_code:
            rule_text = payload.clarified_text
            updated_rule = r.code

        db.add(models.Rule(
            kb_version_id=new_kb.id,
            code=r.code,
            category=r.category,
            text=rule_text,
            severity_default=r.severity_default,
            channels=r.channels,
            examples_good=r.examples_good,
            examples_bad=r.examples_bad,
            source_doc=r.source_doc,
        ))

    # 2. Clone Facts and apply update if targeted
    facts = db.query(models.Fact).filter(models.Fact.kb_version_id == current_kb.id).all()
    updated_fact = None
    for f in facts:
        fact_val = f.value
        fact_valid_to = f.valid_to
        if payload.target_code and f.code == payload.target_code:
            if payload.new_value:
                fact_val = payload.new_value
            elif payload.clarified_text:
                fact_val = payload.clarified_text
            if payload.new_valid_to:
                fact_valid_to = payload.new_valid_to
            else:
                fact_valid_to = utc_now() + datetime.timedelta(days=365)
            updated_fact = f.code

        db.add(models.Fact(
            kb_version_id=new_kb.id,
            code=f.code,
            key=f.key,
            value=fact_val,
            unit=f.unit,
            source=f.source,
            owner=f.owner,
            valid_from=f.valid_from,
            valid_to=fact_valid_to,
        ))

    # 3. Clone Terms and apply resolution if targeted
    terms = db.query(models.Term).filter(models.Term.kb_version_id == current_kb.id).all()
    updated_term = None
    for t in terms:
        banned_list = list(t.banned or [])
        pref = t.preferred
        if payload.signal_type == "conflicting_term":
            if payload.term_preferred and t.preferred.lower() == payload.term_preferred.lower():
                # Remove any conflicted item from banned
                pref = payload.term_preferred
                updated_term = pref
            # Strip target term from banned list if instructed
            if payload.target_code and payload.target_code in banned_list:
                banned_list = [b for b in banned_list if b != payload.target_code]
                updated_term = t.preferred

        db.add(models.Term(
            kb_version_id=new_kb.id,
            preferred=pref,
            banned=banned_list,
            case_rule=t.case_rule,
            notes=t.notes,
        ))

    # 4. Clone Claims
    claims = db.query(models.Claim).filter(models.Claim.kb_version_id == current_kb.id).all()
    for c in claims:
        db.add(models.Claim(
            kb_version_id=new_kb.id,
            approved_text=c.approved_text,
            evidence_ref=c.evidence_ref,
            required_disclaimer=c.required_disclaimer,
            valid_to=c.valid_to,
        ))

    # 5. Clone Assets
    assets = db.query(models.Asset).filter(models.Asset.kb_version_id == current_kb.id).all()
    for a in assets:
        db.add(models.Asset(
            kb_version_id=new_kb.id,
            type=a.type,
            spec_json=a.spec_json,
            file_ref=a.file_ref,
        ))

    db.flush()

    # Log audit event with SHA-256 hash chaining
    log_audit_event(
        db=db,
        workspace_id=ws_id,
        actor_id=current_user.id,
        action="accept_clarification",
        entity="kb_version",
        entity_id=new_kb.id,
        payload={
            "old_kb_version_id": current_kb.id,
            "new_kb_version_id": new_kb.id,
            "signal_type": payload.signal_type,
            "target_code": payload.target_code,
            "clarified_text": payload.clarified_text,
            "updated_rule": updated_rule,
            "updated_fact": updated_fact,
            "updated_term": updated_term,
        },
    )

    db.commit()
    db.refresh(new_kb)

    return {
        "success": True,
        "message": f"Successfully activated new KB version {new_kb.id} with clarified policy.",
        "old_kb_version_id": current_kb.id,
        "new_kb_version_id": new_kb.id,
        "new_kb_label": new_kb.label,
        "is_active": new_kb.is_active,
        "updated": {
            "rule": updated_rule,
            "fact": updated_fact,
            "term": updated_term,
        },
    }
