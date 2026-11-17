import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.config import settings
from ...db import session, models
from ...core.security import get_current_user, require_roles
from .atomise import atomise_guidelines

router = APIRouter(prefix="/kb", tags=["knowledge-base"])

# --- Helper ---
def get_or_create_active_kb(db: Session, workspace_id: int, user_id: int) -> models.KBVersion:
    kb = (
        db.query(models.KBVersion)
        .filter(models.KBVersion.workspace_id == workspace_id, models.KBVersion.is_active == True)
        .first()
    )
    if not kb:
        kb = models.KBVersion(
            workspace_id=workspace_id,
            label="v1.0.0",
            created_by=user_id,
            is_active=True,
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
    return kb

# --- Schemas ---
class RuleSchema(BaseModel):
    code: str
    category: str
    text: str
    severity_default: str = "minor"
    channels: Optional[List[str]] = None
    examples_good: Optional[List[str]] = None
    examples_bad: Optional[List[str]] = None
    source_doc: Optional[str] = None

class FactSchema(BaseModel):
    code: str
    key: str
    value: str
    unit: Optional[str] = None
    source: Optional[str] = None
    owner: Optional[str] = None

class TermSchema(BaseModel):
    preferred: str
    banned: Optional[List[str]] = None
    case_rule: Optional[str] = None
    notes: Optional[str] = None

class ClaimSchema(BaseModel):
    approved_text: str
    evidence_ref: Optional[str] = None
    required_disclaimer: Optional[str] = None

class AssetSchema(BaseModel):
    type: str
    spec_json: Optional[Dict[str, Any]] = None
    file_ref: Optional[str] = None

class AtomiseRequest(BaseModel):
    guidelines_text: str

class ConfirmImportRequest(BaseModel):
    rules: Optional[List[RuleSchema]] = None
    facts: Optional[List[FactSchema]] = None
    terms: Optional[List[TermSchema]] = None
    claims: Optional[List[ClaimSchema]] = None

class CreateVersionRequest(BaseModel):
    label: str

# --- Endpoints ---

@router.get("/rules")
def list_rules(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    return db.query(models.Rule).filter(models.Rule.kb_version_id == kb.id).all()

@router.post("/rules", status_code=201)
def create_rule(
    payload: RuleSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    rule = models.Rule(
        kb_version_id=kb.id,
        code=payload.code,
        category=payload.category,
        text=payload.text,
        severity_default=payload.severity_default,
        channels=payload.channels,
        examples_good=payload.examples_good,
        examples_bad=payload.examples_bad,
        source_doc=payload.source_doc,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/rules/{rule_id}", status_code=200)
def delete_rule(
    rule_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    rule = db.query(models.Rule).filter(models.Rule.id == rule_id, models.Rule.kb_version_id == kb.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"status": "deleted", "rule_id": rule_id}

@router.get("/facts")
def list_facts(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    return db.query(models.Fact).filter(models.Fact.kb_version_id == kb.id).all()

@router.post("/facts", status_code=201)
def create_fact(
    payload: FactSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    fact = models.Fact(
        kb_version_id=kb.id,
        code=payload.code,
        key=payload.key,
        value=payload.value,
        unit=payload.unit,
        source=payload.source,
        owner=payload.owner,
    )
    db.add(fact)
    db.commit()
    db.refresh(fact)
    return fact

@router.get("/terms")
def list_terms(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    return db.query(models.Term).filter(models.Term.kb_version_id == kb.id).all()

@router.post("/terms", status_code=201)
def create_term(
    payload: TermSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    term = models.Term(
        kb_version_id=kb.id,
        preferred=payload.preferred,
        banned=payload.banned,
        case_rule=payload.case_rule,
        notes=payload.notes,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term

@router.get("/claims")
def list_claims(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    return db.query(models.Claim).filter(models.Claim.kb_version_id == kb.id).all()

@router.post("/claims", status_code=201)
def create_claim(
    payload: ClaimSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    claim = models.Claim(
        kb_version_id=kb.id,
        approved_text=payload.approved_text,
        evidence_ref=payload.evidence_ref,
        required_disclaimer=payload.required_disclaimer,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim

@router.get("/assets")
def list_assets(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    return db.query(models.Asset).filter(models.Asset.kb_version_id == kb.id).all()

@router.post("/assets", status_code=201)
def create_asset(
    payload: AssetSchema,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    asset = models.Asset(
        kb_version_id=kb.id,
        type=payload.type,
        spec_json=payload.spec_json,
        file_ref=payload.file_ref,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset

# --- Atomisation and Confirmation Flow ---

@router.post("/atomise")
def atomise_endpoint(
    payload: AtomiseRequest,
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    candidates = atomise_guidelines(payload.guidelines_text)
    return {"total_candidates": len(candidates), "candidates": candidates}

@router.post("/confirm-import", status_code=201)
def confirm_import(
    payload: ConfirmImportRequest,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    saved_rules = 0
    saved_facts = 0
    saved_terms = 0
    saved_claims = 0

    if payload.rules:
        for r in payload.rules:
            rule = models.Rule(
                kb_version_id=kb.id,
                code=r.code,
                category=r.category,
                text=r.text,
                severity_default=r.severity_default,
                channels=r.channels,
                examples_good=r.examples_good,
                examples_bad=r.examples_bad,
                source_doc=r.source_doc,
            )
            db.add(rule)
            saved_rules += 1

    if payload.facts:
        for f in payload.facts:
            fact = models.Fact(
                kb_version_id=kb.id,
                code=f.code,
                key=f.key,
                value=f.value,
                unit=f.unit,
                source=f.source,
                owner=f.owner,
            )
            db.add(fact)
            saved_facts += 1

    if payload.terms:
        for t in payload.terms:
            term = models.Term(
                kb_version_id=kb.id,
                preferred=t.preferred,
                banned=t.banned,
                case_rule=t.case_rule,
                notes=t.notes,
            )
            db.add(term)
            saved_terms += 1

    if payload.claims:
        for c in payload.claims:
            claim = models.Claim(
                kb_version_id=kb.id,
                approved_text=c.approved_text,
                evidence_ref=c.evidence_ref,
                required_disclaimer=c.required_disclaimer,
            )
            db.add(claim)
            saved_claims += 1

    db.commit()
    return {
        "status": "imported",
        "kb_version_id": kb.id,
        "saved_rules": saved_rules,
        "saved_facts": saved_facts,
        "saved_terms": saved_terms,
        "saved_claims": saved_claims,
    }

# --- Versioning ---

@router.get("/versions")
def list_versions(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.KBVersion)
        .filter(models.KBVersion.workspace_id == current_user.workspace_id)
        .order_by(models.KBVersion.id.desc())
        .all()
    )

@router.post("/versions", status_code=201)
def create_new_version(
    payload: CreateVersionRequest,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    current_kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    # Deactivate current
    current_kb.is_active = False

    # Create new snapshot version
    new_kb = models.KBVersion(
        workspace_id=current_user.workspace_id,
        label=payload.label,
        created_by=current_user.id,
        is_active=True,
    )
    db.add(new_kb)
    db.flush()

    # Clone rules into new version
    existing_rules = db.query(models.Rule).filter(models.Rule.kb_version_id == current_kb.id).all()
    for r in existing_rules:
        new_rule = models.Rule(
            kb_version_id=new_kb.id,
            code=r.code,
            category=r.category,
            text=r.text,
            severity_default=r.severity_default,
            channels=r.channels,
            examples_good=r.examples_good,
            examples_bad=r.examples_bad,
            source_doc=r.source_doc,
        )
        db.add(new_rule)

    db.commit()
    db.refresh(new_kb)
    return {
        "id": new_kb.id,
        "label": new_kb.label,
        "is_active": new_kb.is_active,
        "cloned_rules": len(existing_rules),
    }

@router.post("/versions/{version_id}/activate")
def activate_version(
    version_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    target_kb = (
        db.query(models.KBVersion)
        .filter(models.KBVersion.id == version_id, models.KBVersion.workspace_id == current_user.workspace_id)
        .first()
    )
    if not target_kb:
        raise HTTPException(status_code=404, detail="KB version not found in workspace")

    # Set all other versions to inactive
    db.query(models.KBVersion).filter(models.KBVersion.workspace_id == current_user.workspace_id).update({"is_active": False})
    target_kb.is_active = True
    db.commit()
    return {"status": "activated", "active_version_id": target_kb.id, "label": target_kb.label}
