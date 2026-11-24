from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ...core.config import settings
from ...db import models, session
from ...schemas import UserCreate, UserResponse, LoginRequest, LoginResponse, Token, WorkspaceInfoWithUsers, DemoAccountInfo
from ...core.security import hash_password, create_access_token, verify_password, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=LoginResponse)
def signup(user: UserCreate, db: Session = Depends(session.get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    workspace = db.query(models.Workspace).first()
    if not workspace:
        workspace = models.Workspace(name="NovaFit")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
    pwd_hash = hash_password(user.password)
    db_user = models.User(
        workspace_id=workspace.id,
        email=user.email,
        name=user.name or user.email.split("@")[0],
        role=user.role,
        password_hash=pwd_hash,
        active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = create_access_token({"sub": str(db_user.id)})
    
    user_resp = UserResponse(
        id=db_user.id,
        email=db_user.email,
        name=db_user.name,
        role=db_user.role if isinstance(db_user.role, str) else db_user.role.value,
        workspace_id=db_user.workspace_id,
        workspace_name=workspace.name,
        active=db_user.active,
    )
    return LoginResponse(access_token=access_token, user=user_resp)

@router.post("/login", response_model=LoginResponse)
def login(
    payload: Optional[LoginRequest] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    db: Session = Depends(session.get_db),
):
    # Support both JSON payload and query parameters
    req_email = payload.email if payload else email
    req_password = payload.password if payload else password

    if not req_email or not req_password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    user = db.query(models.User).filter(models.User.email == req_email).first()
    if not user or not verify_password(req_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.active:
        raise HTTPException(status_code=403, detail="User account is deactivated")

    workspace = db.query(models.Workspace).filter(models.Workspace.id == user.workspace_id).first()
    workspace_name = workspace.name if workspace else "Default Workspace"

    access_token = create_access_token({"sub": str(user.id)})
    role_str = user.role if isinstance(user.role, str) else user.role.value

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        name=user.name or user.email.split("@")[0],
        role=role_str,
        workspace_id=user.workspace_id,
        workspace_name=workspace_name,
        active=user.active,
    )
    return LoginResponse(access_token=access_token, user=user_resp)

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(session.get_db),
):
    workspace = db.query(models.Workspace).filter(models.Workspace.id == current_user.workspace_id).first()
    role_str = current_user.role if isinstance(current_user.role, str) else current_user.role.value
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=role_str,
        workspace_id=current_user.workspace_id,
        workspace_name=workspace.name if workspace else "Unknown",
        active=current_user.active,
    )

@router.get("/workspaces", response_model=List[WorkspaceInfoWithUsers])
def list_workspaces_with_demo_accounts(db: Session = Depends(session.get_db)):
    """Returns all available workspaces with their users for the demo switcher.
    Allows real authentic logins across NovaFit, Lumen Bank, and Aster University.
    """
    workspaces = db.query(models.Workspace).order_by(models.Workspace.id.asc()).all()
    results = []
    for ws in workspaces:
        users = db.query(models.User).filter(models.User.workspace_id == ws.id).all()
        accounts = [
            DemoAccountInfo(
                id=u.id,
                email=u.email,
                name=u.name or u.email.split("@")[0],
                role=u.role if isinstance(u.role, str) else u.role.value,
                workspace_id=ws.id,
                workspace_name=ws.name,
            )
            for u in users
        ]
        results.append(
            WorkspaceInfoWithUsers(
                id=ws.id,
                name=ws.name,
                confidential_tier=ws.confidential_tier,
                ai_mode=ws.ai_mode,
                accounts=accounts,
            )
        )
    return results
