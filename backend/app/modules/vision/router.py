from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from ...db import session, models
from ...core.security import get_current_user
from .analyzer import analyze_image_brand_consistency

router = APIRouter(prefix="/vision", tags=["vision"])

@router.post("/analyze")
def analyze_image_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Fetch active brand palette from KB if available
    kb = (
        db.query(models.KBVersion)
        .filter(models.KBVersion.workspace_id == current_user.workspace_id, models.KBVersion.is_active == True)
        .first()
    )
    palette = None
    if kb:
        asset = (
            db.query(models.Asset)
            .filter(models.Asset.kb_version_id == kb.id, models.Asset.type == "palette")
            .first()
        )
        if asset and asset.spec_json:
            palette = list(asset.spec_json.values())

    try:
        results = analyze_image_brand_consistency(data, approved_palette_hex=palette)
        return {
            "filename": file.filename,
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image analysis error: {str(e)}")
