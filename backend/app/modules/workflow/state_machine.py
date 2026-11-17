"""Workflow state machine and risk-based escalation rules for BrandSentinel.
Governs transitions:
draft -> ai_checked -> revising -> submitted -> manager_review -> (escalated) -> approved / changes_requested / rejected
"""

from typing import List, Dict, Any, Tuple
from fastapi import HTTPException, status
from ...db import models

VALID_TRANSITIONS = {
    "draft": ["ai_checked", "revising", "submitted"],
    "ai_checked": ["revising", "submitted", "manager_review", "escalated", "approved", "changes_requested"],
    "revising": ["submitted", "ai_checked"],
    "submitted": ["manager_review", "escalated", "approved", "changes_requested"],
    "manager_review": ["approved", "changes_requested", "escalated", "rejected"],
    "escalated": ["approved", "changes_requested", "rejected"],
    "changes_requested": ["revising", "draft"],
    "approved": ["revising"],  # creating a new version
    "rejected": ["revising"],
}

def can_transition(from_status: str, to_status: str) -> bool:
    allowed = VALID_TRANSITIONS.get(from_status, [])
    return to_status in allowed

def validate_transition(from_status: str, to_status: str) -> None:
    if not can_transition(from_status, to_status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition: Cannot transition from '{from_status}' to '{to_status}'",
        )

def evaluate_escalation(
    findings: List[Any],
    risk_rules: List[Any],
) -> Tuple[bool, str]:
    """Check if content must be escalated to an Authorised Reviewer.
    Triggers on:
    - Any finding with severity 'blocker'
    - Any finding with confidence < 0.70
    - Any custom workspace RiskRule condition matching
    """
    for f in findings:
        sev = getattr(f, "severity", None) or f.get("severity")
        if sev == "blocker":
            return True, f"Blocker severity finding detected: {getattr(f, 'reason', '') or f.get('reason', '')}"

        conf_raw = getattr(f, "confidence", None) or f.get("confidence")
        try:
            conf = float(conf_raw)
            if conf < 0.70:
                return True, f"Low-confidence AI finding ({conf:.2f} < 0.70) requires human reviewer signoff"
        except (ValueError, TypeError):
            pass

    for rr in risk_rules:
        cond = rr.condition_json or {}
        req_sev = cond.get("min_severity")
        req_cat = cond.get("category")
        for f in findings:
            f_sev = getattr(f, "severity", None) or f.get("severity")
            f_cat = getattr(f, "category", None) or f.get("category")
            if (not req_sev or f_sev == req_sev) and (not req_cat or f_cat == req_cat):
                return True, f"Matched workspace risk rule: {rr.description or 'Custom rule matched'}"

    return False, ""
