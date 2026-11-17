from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import uuid
import hashlib
import json

from ..core.config import settings
from ..db import session, models
from ..schemas import Token
from ..core.security import get_current_user
from ..modules.ai_providers.mock import MockProvider

router = APIRouter(prefix="/content", tags=["content"])

@router.post("/", status_code=201)
def create_content(title: str, type: str, channel: str = None, file: UploadFile = File(None), db: Session = Depends(session.get_db), user_id: int = Depends(get_current_user)):
    # Simple content creation, store file reference if provided
    content = models.Content(
        workspace_id=1,  # placeholder – real workspace lookup omitted
        creator_id=user_id,
        title=title,
        type=type,
        channel=channel,
        status="draft",
    )
    db.add(content)
    db.flush()
    # create initial version
    body = ""
    file_ref = None
    if file:
        data = file.file.read()
        # store file under ./uploads/<uuid>
        fname = f"uploads/{uuid.uuid4().hex}_{file.filename}"
        with open(fname, "wb") as f:
            f.write(data)
        file_ref = fname
        if type == "text":
            body = data.decode(errors="ignore")
    content_hash = hashlib.sha256((body + (file_ref or "")).encode()).hexdigest()
    version = models.ContentVersion(
        content_id=content.id,
        version_no=1,
        text_body=body,
        file_ref=file_ref,
        content_hash=content_hash,
        created_by=user_id,
    )
    db.add(version)
    db.flush()
    content.current_version_id = version.id
    db.commit()
    return {"content_id": content.id, "version_id": version.id}

@router.post("/{content_id}/review", status_code=202)
def review_content(content_id: int, db: Session = Depends(session.get_db), user_id: int = Depends(get_current_user)):
    # Find latest version
    content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    version = db.query(models.ContentVersion).filter(models.ContentVersion.id == content.current_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    # Create review run
    review = models.ReviewRun(
        version_id=version.id,
        kb_version_id=1,  # placeholder default KB
        provider="mock" if not settings.gemini_api_key else "gemini",
        model=settings.llm_model,
        status="running",
    )
    db.add(review)
    db.commit()
    # Run simple mock pipeline synchronously
    provider = MockProvider()
    findings = provider.generate_json(prompt=version.text_body, schema={"findings": []}, purpose="review")
    # store findings (none in mock)
    review.status = "completed"
    db.commit()
    return {"review_id": review.id, "status": review.status, "findings": findings["findings"]}
