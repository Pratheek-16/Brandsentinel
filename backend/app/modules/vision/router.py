import io
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from PIL import Image

from ...db import session, models
from ...core.security import get_current_user
from ...core.config import settings
from .analyzer import inspect_asset_accessibility, check_ocr_availability

router = APIRouter(prefix="/vision", tags=["vision"])


@router.get("/ocr-status")
def get_ocr_status(current_user: models.User = Depends(get_current_user)):
    """Return explicit host OCR engine availability status."""
    return check_ocr_availability()


@router.post("/analyze")
def analyze_image_endpoint(
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    logo_file: Optional[UploadFile] = File(None),
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user),
):
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(data) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size limit of {settings.max_upload_size_bytes // (1024*1024)}MB."
        )

    # Resolve active brand palette from KB
    kb = (
        db.query(models.KBVersion)
        .filter(models.KBVersion.workspace_id == current_user.workspace_id, models.KBVersion.is_active == True)
        .first()
    )
    palette = None
    brand_name = None
    if kb:
        brand_name = current_user.workspace.name if current_user.workspace else None
        asset = (
            db.query(models.Asset)
            .filter(models.Asset.kb_version_id == kb.id, models.Asset.type == "palette")
            .first()
        )
        if asset and asset.spec_json:
            spec = asset.spec_json
            if isinstance(spec, dict) and "colors" in spec:
                palette = spec["colors"]
            elif isinstance(spec, dict):
                palette = list(spec.values())
            elif isinstance(spec, list):
                palette = spec

    filename = file.filename or "uploaded_asset"

    logo_bytes = None
    if logo_file:
        try:
            logo_bytes = logo_file.file.read()
        except Exception:
            logo_bytes = None

    try:
        results = inspect_asset_accessibility(
            file_bytes=data,
            filename=filename,
            approved_palette_hex=palette,
            alt_text=alt_text,
            logo_template_bytes=logo_bytes,
            brand_name=brand_name,
        )
        return {
            "filename": filename,
            "results": results,
            **results,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Visual asset inspection error: {str(e)}")
