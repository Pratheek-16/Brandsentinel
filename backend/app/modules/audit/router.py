from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...db import session, models
from ...core.security import get_current_user
from .chain import verify_audit_chain

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/")
def list_audit_events(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    events = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.workspace_id == current_user.workspace_id)
        .order_by(models.AuditEvent.id.desc())
        .limit(100)
        .all()
    )
    return events

@router.get("/verify")
def verify_audit_log(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    is_valid, count, details = verify_audit_chain(db, current_user.workspace_id)
    return {
        "workspace_id": current_user.workspace_id,
        "is_valid": is_valid,
        "total_events": count,
        "details": details,
    }
