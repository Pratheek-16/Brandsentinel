from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.config import settings
from ...db import models, session

router = APIRouter(prefix="/kb", tags=["knowledge-base"])

@router.get("/workspaces")
def list_workspaces(db: Session = Depends(session.get_db)):
    return db.query(models.Workspace).all()
