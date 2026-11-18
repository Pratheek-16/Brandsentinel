import io
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from PIL import Image
import pdfplumber

from ...db import session, models
from ...core.security import get_current_user
from ...core.config import settings
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
    if kb:
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
    lower_name = filename.lower()

    # Handle PDF by extracting rendered first page
    image_bytes = data
    if lower_name.endswith(".pdf"):
        try:
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                if not pdf.pages:
                    raise HTTPException(status_code=400, detail="PDF has no pages.")
                first_page = pdf.pages[0]
                # Render page to image
                page_img = first_page.to_image(resolution=150).original
                buf = io.BytesIO()
                page_img.save(buf, format="PNG")
                image_bytes = buf.getvalue()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not render PDF for visual analysis: {str(e)}")

    try:
        results = analyze_image_brand_consistency(
            image_bytes=image_bytes,
            approved_palette_hex=palette,
            filename=filename,
        )
        return {
            "filename": filename,
            "results": results,
            **results,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Visual asset inspection error: {str(e)}")
