from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from ..core.config import settings
from ..core.security import hash_password, verify_password, create_access_token
from ..db.session import get_db
from ..db import models
from ..schemas import UserCreate, Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=Token)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    # find or create a workspace for demo if needed – placeholder default workspace 1
    workspace = db.query(models.Workspace).first()
    if not workspace:
        workspace = models.Workspace(name="default")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
    pwd_hash = hash_password(user.password)
    db_user = models.User(
        workspace_id=workspace.id,
        email=user.email,
        name=user.name,
        role=user.role,
        password_hash=pwd_hash,
        active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = create_access_token({"sub": str(db_user.id)})
    return Token(access_token=access_token)

@router.post("/login", response_model=Token)
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token)
