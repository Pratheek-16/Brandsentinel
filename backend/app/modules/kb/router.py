import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.config import settings
from ...db import session, models
from ...core.security import get_current_user, require_roles
from ...core.datetime_utils import utc_now
from ...schemas import (
    RuleCreate, RuleUpdate, RuleResponse,
    FactCreate, FactUpdate, FactResponse,
    TermCreate, TermUpdate, TermResponse,
    ClaimCreate, ClaimUpdate, ClaimResponse,
    AssetCreate, AssetResponse,
    KBVersionResponse
)
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
            label="Approved Guidelines v1.0",
            created_by=user_id,
            is_active=True,
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
    return kb

# --- Rules CRUD ---

@router.get("/rules", response_model=List[RuleResponse])
def list_rules(
    category: Optional[str] = None,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    query = db.query(models.Rule).filter(models.Rule.kb_version_id == kb.id)
    if category:
        query = query.filter(models.Rule.category == category)
    return query.order_by(models.Rule.id.asc()).all()

@router.post("/rules", status_code=201, response_model=RuleResponse)
def create_rule(
    payload: RuleCreate,
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

@router.put("/rules/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: int,
    payload: RuleUpdate,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    rule = db.query(models.Rule).filter(models.Rule.id == rule_id, models.Rule.kb_version_id == kb.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found in active KB version")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, val)

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
        raise HTTPException(status_code=404, detail="Rule not found in active KB version")
    db.delete(rule)
    db.commit()
    return {"status": "deleted", "rule_id": rule_id}

# --- Facts CRUD ---

@router.get("/facts", response_model=List[FactResponse])
def list_facts(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    facts = db.query(models.Fact).filter(models.Fact.kb_version_id == kb.id).order_by(models.Fact.id.asc()).all()
    now = utc_now()
    results = []
    for f in facts:
        is_stale = bool(f.valid_to and f.valid_to < now)
        f_dict = FactResponse(
            id=f.id,
            kb_version_id=f.kb_version_id,
            code=f.code,
            key=f.key,
            value=f.value,
            unit=f.unit,
            source=f.source,
            owner=f.owner,
            valid_from=f.valid_from,
            valid_to=f.valid_to,
            is_stale=is_stale,
        )
        results.append(f_dict)
    return results

@router.post("/facts", status_code=201, response_model=FactResponse)
def create_fact(
    payload: FactCreate,
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
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
    )
    db.add(fact)
    db.commit()
    db.refresh(fact)
    now = utc_now()
    return FactResponse(
        id=fact.id,
        kb_version_id=fact.kb_version_id,
        code=fact.code,
        key=fact.key,
        value=fact.value,
        unit=fact.unit,
        source=fact.source,
        owner=fact.owner,
        valid_from=fact.valid_from,
        valid_to=fact.valid_to,
        is_stale=bool(fact.valid_to and fact.valid_to < now),
    )

@router.put("/facts/{fact_id}", response_model=FactResponse)
def update_fact(
    fact_id: int,
    payload: FactUpdate,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    fact = db.query(models.Fact).filter(models.Fact.id == fact_id, models.Fact.kb_version_id == kb.id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found in active KB version")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(fact, field, val)

    db.commit()
    db.refresh(fact)
    now = utc_now()
    return FactResponse(
        id=fact.id,
        kb_version_id=fact.kb_version_id,
        code=fact.code,
        key=fact.key,
        value=fact.value,
        unit=fact.unit,
        source=fact.source,
        owner=fact.owner,
        valid_from=fact.valid_from,
        valid_to=fact.valid_to,
        is_stale=bool(fact.valid_to and fact.valid_to < now),
    )

@router.delete("/facts/{fact_id}", status_code=200)
def delete_fact(
    fact_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    fact = db.query(models.Fact).filter(models.Fact.id == fact_id, models.Fact.kb_version_id == kb.id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found in active KB version")
    db.delete(fact)
    db.commit()
    return {"status": "deleted", "fact_id": fact_id}

# --- Terms CRUD ---

@router.get("/terms", response_model=List[TermResponse])
def list_terms(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    return db.query(models.Term).filter(models.Term.kb_version_id == kb.id).order_by(models.Term.id.asc()).all()

@router.post("/terms", status_code=201, response_model=TermResponse)
def create_term(
    payload: TermCreate,
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

@router.put("/terms/{term_id}", response_model=TermResponse)
def update_term(
    term_id: int,
    payload: TermUpdate,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    term = db.query(models.Term).filter(models.Term.id == term_id, models.Term.kb_version_id == kb.id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found in active KB version")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(term, field, val)

    db.commit()
    db.refresh(term)
    return term

@router.delete("/terms/{term_id}", status_code=200)
def delete_term(
    term_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    term = db.query(models.Term).filter(models.Term.id == term_id, models.Term.kb_version_id == kb.id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found in active KB version")
    db.delete(term)
    db.commit()
    return {"status": "deleted", "term_id": term_id}

# --- Claims CRUD ---

@router.get("/claims", response_model=List[ClaimResponse])
def list_claims(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    claims = db.query(models.Claim).filter(models.Claim.kb_version_id == kb.id).order_by(models.Claim.id.asc()).all()
    now = utc_now()
    results = []
    for c in claims:
        is_expired = bool(c.valid_to and c.valid_to < now)
        results.append(ClaimResponse(
            id=c.id,
            kb_version_id=c.kb_version_id,
            approved_text=c.approved_text,
            evidence_ref=c.evidence_ref,
            required_disclaimer=c.required_disclaimer,
            valid_to=c.valid_to,
            is_expired=is_expired,
        ))
    return results

@router.post("/claims", status_code=201, response_model=ClaimResponse)
def create_claim(
    payload: ClaimCreate,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    claim = models.Claim(
        kb_version_id=kb.id,
        approved_text=payload.approved_text,
        evidence_ref=payload.evidence_ref,
        required_disclaimer=payload.required_disclaimer,
        valid_to=payload.valid_to,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    now = utc_now()
    return ClaimResponse(
        id=claim.id,
        kb_version_id=claim.kb_version_id,
        approved_text=claim.approved_text,
        evidence_ref=claim.evidence_ref,
        required_disclaimer=claim.required_disclaimer,
        valid_to=claim.valid_to,
        is_expired=bool(claim.valid_to and claim.valid_to < now),
    )

@router.put("/claims/{claim_id}", response_model=ClaimResponse)
def update_claim(
    claim_id: int,
    payload: ClaimUpdate,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id, models.Claim.kb_version_id == kb.id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found in active KB version")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(claim, field, val)

    db.commit()
    db.refresh(claim)
    now = utc_now()
    return ClaimResponse(
        id=claim.id,
        kb_version_id=claim.kb_version_id,
        approved_text=claim.approved_text,
        evidence_ref=claim.evidence_ref,
        required_disclaimer=claim.required_disclaimer,
        valid_to=claim.valid_to,
        is_expired=bool(claim.valid_to and claim.valid_to < now),
    )

@router.delete("/claims/{claim_id}", status_code=200)
def delete_claim(
    claim_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id, models.Claim.kb_version_id == kb.id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found in active KB version")
    db.delete(claim)
    db.commit()
    return {"status": "deleted", "claim_id": claim_id}

# --- Assets CRUD ---

@router.get("/assets", response_model=List[AssetResponse])
def list_assets(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    return db.query(models.Asset).filter(models.Asset.kb_version_id == kb.id).all()

@router.post("/assets", status_code=201, response_model=AssetResponse)
def create_asset(
    payload: AssetCreate,
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

@router.delete("/assets/{asset_id}", status_code=200)
def delete_asset(
    asset_id: int,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    asset = db.query(models.Asset).filter(models.Asset.id == asset_id, models.Asset.kb_version_id == kb.id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found in active KB version")
    db.delete(asset)
    db.commit()
    return {"status": "deleted", "asset_id": asset_id}

# --- Atomisation & Confirmation Flow ---

class AtomiseRequest(Dict[str, Any]):
    pass

@router.post("/atomise")
def atomise_endpoint(
    payload: Dict[str, Any],
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    text = payload.get("guidelines_text") or payload.get("raw_text") or ""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Guidelines text cannot be empty")
    candidates = atomise_guidelines(text)
    return {"total_candidates": len(candidates), "candidates": candidates}

@router.post("/confirm-import", status_code=201)
def confirm_import(
    payload: Dict[str, Any],
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    saved_rules = 0
    saved_facts = 0
    saved_terms = 0
    saved_claims = 0

    rules_in = payload.get("rules", [])
    for r in rules_in:
        rule = models.Rule(
            kb_version_id=kb.id,
            code=r.get("code") or f"RULE-{saved_rules+1}",
            category=r.get("category", "messaging"),
            text=r.get("text", ""),
            severity_default=r.get("severity_default", "minor"),
            channels=r.get("channels"),
            examples_good=r.get("examples_good"),
            examples_bad=r.get("examples_bad"),
            source_doc=r.get("source_doc", "Imported Policy"),
        )
        db.add(rule)
        saved_rules += 1

    facts_in = payload.get("facts", [])
    for f in facts_in:
        fact = models.Fact(
            kb_version_id=kb.id,
            code=f.get("code") or f"FACT-{saved_facts+1}",
            key=f.get("key", ""),
            value=f.get("value", ""),
            unit=f.get("unit"),
            source=f.get("source", "Imported Policy"),
            owner=f.get("owner", "Brand Guardian"),
        )
        db.add(fact)
        saved_facts += 1

    terms_in = payload.get("terms", [])
    for t in terms_in:
        term = models.Term(
            kb_version_id=kb.id,
            preferred=t.get("preferred", ""),
            banned=t.get("banned", []),
            case_rule=t.get("case_rule"),
            notes=t.get("notes"),
        )
        db.add(term)
        saved_terms += 1

    claims_in = payload.get("claims", [])
    for c in claims_in:
        claim = models.Claim(
            kb_version_id=kb.id,
            approved_text=c.get("approved_text", ""),
            evidence_ref=c.get("evidence_ref"),
            required_disclaimer=c.get("required_disclaimer"),
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

# --- Versioning & Complete Snapshot Cloning ---

@router.get("/versions", response_model=List[KBVersionResponse])
def list_versions(
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    versions = (
        db.query(models.KBVersion)
        .filter(models.KBVersion.workspace_id == current_user.workspace_id)
        .order_by(models.KBVersion.id.desc())
        .all()
    )
    results = []
    for v in versions:
        r_cnt = db.query(models.Rule).filter(models.Rule.kb_version_id == v.id).count()
        f_cnt = db.query(models.Fact).filter(models.Fact.kb_version_id == v.id).count()
        t_cnt = db.query(models.Term).filter(models.Term.kb_version_id == v.id).count()
        c_cnt = db.query(models.Claim).filter(models.Claim.kb_version_id == v.id).count()
        a_cnt = db.query(models.Asset).filter(models.Asset.kb_version_id == v.id).count()
        results.append(KBVersionResponse(
            id=v.id,
            workspace_id=v.workspace_id,
            label=v.label,
            is_active=v.is_active,
            created_at=v.created_at,
            created_by=v.created_by,
            rules_count=r_cnt,
            facts_count=f_cnt,
            terms_count=t_cnt,
            claims_count=c_cnt,
            assets_count=a_cnt,
        ))
    return results

@router.post("/versions", status_code=201)
def create_new_version(
    payload: Dict[str, str],
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(require_roles(models.RoleEnum.admin)),
):
    label = payload.get("label") or f"Guidelines Snapshot {utc_now().strftime('%Y-%m-%d %H:%M')}"
    current_kb = get_or_create_active_kb(db, current_user.workspace_id, current_user.id)
    current_kb.is_active = False

    # Create new snapshot version
    new_kb = models.KBVersion(
        workspace_id=current_user.workspace_id,
        label=label,
        created_by=current_user.id,
        is_active=True,
    )
    db.add(new_kb)
    db.flush()

    # 1. Clone Rules
    rules = db.query(models.Rule).filter(models.Rule.kb_version_id == current_kb.id).all()
    for r in rules:
        db.add(models.Rule(
            kb_version_id=new_kb.id,
            code=r.code,
            category=r.category,
            text=r.text,
            severity_default=r.severity_default,
            channels=r.channels,
            examples_good=r.examples_good,
            examples_bad=r.examples_bad,
            source_doc=r.source_doc,
        ))

    # 2. Clone Facts
    facts = db.query(models.Fact).filter(models.Fact.kb_version_id == current_kb.id).all()
    for f in facts:
        db.add(models.Fact(
            kb_version_id=new_kb.id,
            code=f.code,
            key=f.key,
            value=f.value,
            unit=f.unit,
            source=f.source,
            owner=f.owner,
            valid_from=f.valid_from,
            valid_to=f.valid_to,
        ))

    # 3. Clone Terms
    terms = db.query(models.Term).filter(models.Term.kb_version_id == current_kb.id).all()
    for t in terms:
        db.add(models.Term(
            kb_version_id=new_kb.id,
            preferred=t.preferred,
            banned=t.banned,
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

    db.commit()
    db.refresh(new_kb)

    return {
        "id": new_kb.id,
        "label": new_kb.label,
        "is_active": new_kb.is_active,
        "cloned_rules": len(rules),
        "cloned_facts": len(facts),
        "cloned_terms": len(terms),
        "cloned_claims": len(claims),
        "cloned_assets": len(assets),
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
        raise HTTPException(status_code=404, detail="KB version not found in active workspace")

    # Set all other versions to inactive
    db.query(models.KBVersion).filter(models.KBVersion.workspace_id == current_user.workspace_id).update({"is_active": False})
    target_kb.is_active = True
    db.commit()
    return {"status": "activated", "active_version_id": target_kb.id, "label": target_kb.label}
