"""Cryptographic Hash-Chained Audit Log for BrandSentinel.
Every governance action (creation, review, edit, comment, approval, escalation) appends
an event whose SHA-256 hash depends on the previous event's hash, forming an immutable,
tamper-evident Merkle/blockchain-style audit trail.
"""

import json
import hashlib
import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from ...db import models
from ...core.datetime_utils import utc_now

GENESIS_HASH = "0" * 64

def compute_event_hash(
    prev_hash: str,
    actor_id: int,
    action: str,
    entity: str,
    entity_id: int,
    payload: Dict[str, Any],
    ts_iso: str,
) -> str:
    canonical_payload = json.dumps(payload or {}, sort_keys=True)
    raw = f"{prev_hash}|{actor_id}|{action}|{entity}|{entity_id}|{canonical_payload}|{ts_iso}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def log_audit_event(
    db: Session,
    workspace_id: int,
    actor_id: int,
    action: str,
    entity: str,
    entity_id: int,
    payload: Dict[str, Any] = None,
) -> models.AuditEvent:
    last_event = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.workspace_id == workspace_id)
        .order_by(models.AuditEvent.id.desc())
        .first()
    )
    prev_hash = last_event.hash if last_event else GENESIS_HASH
    now = utc_now()
    ts_iso = now.isoformat()

    h = compute_event_hash(
        prev_hash=prev_hash,
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        payload=payload or {},
        ts_iso=ts_iso,
    )

    event = models.AuditEvent(
        workspace_id=workspace_id,
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        payload_json=payload or {},
        prev_hash=prev_hash,
        hash=h,
        ts=now,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def verify_audit_chain(db: Session, workspace_id: int) -> Tuple[bool, int, Dict[str, Any]]:
    """Verify cryptographic integrity of the entire audit chain for a workspace.
    Returns (is_valid, total_events, details).
    """
    events = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.workspace_id == workspace_id)
        .order_by(models.AuditEvent.id.asc())
        .all()
    )
    if not events:
        return True, 0, {"message": "Audit chain empty", "head_hash": GENESIS_HASH}

    expected_prev = GENESIS_HASH
    for idx, ev in enumerate(events):
        if ev.prev_hash != expected_prev:
            return False, len(events), {
                "error": f"Broken chain link at event ID {ev.id} (index {idx})",
                "event_id": ev.id,
                "stored_prev_hash": ev.prev_hash,
                "expected_prev_hash": expected_prev,
            }

        recomputed = compute_event_hash(
            prev_hash=ev.prev_hash,
            actor_id=ev.actor_id,
            action=ev.action,
            entity=ev.entity,
            entity_id=ev.entity_id,
            payload=ev.payload_json or {},
            ts_iso=ev.ts.isoformat(),
        )
        if recomputed != ev.hash:
            return False, len(events), {
                "error": f"Tampered event payload at event ID {ev.id}",
                "event_id": ev.id,
                "stored_hash": ev.hash,
                "recomputed_hash": recomputed,
            }
        expected_prev = ev.hash

    return True, len(events), {
        "status": "verified",
        "total_events": len(events),
        "head_hash": events[-1].hash,
    }
