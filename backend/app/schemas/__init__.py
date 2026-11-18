from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    password: str = Field(min_length=8)
    role: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: str
    workspace_id: int
    workspace_name: Optional[str] = None
    active: bool = True

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class WorkspaceResponse(BaseModel):
    id: int
    name: str
    confidential_tier: str
    ai_mode: str
    retention_days: int

    class Config:
        from_attributes = True

class DemoAccountInfo(BaseModel):
    id: int
    email: str
    name: str
    role: str
    workspace_id: int
    workspace_name: str

class WorkspaceInfoWithUsers(BaseModel):
    id: int
    name: str
    confidential_tier: str
    ai_mode: str
    accounts: List[DemoAccountInfo]

# --- Knowledge Base Schemas ---

class RuleBase(BaseModel):
    code: str
    category: str
    text: str
    severity_default: str = "minor"
    channels: Optional[List[str]] = None
    examples_good: Optional[List[str]] = None
    examples_bad: Optional[List[str]] = None
    source_doc: Optional[str] = None

class RuleCreate(RuleBase):
    pass

class RuleUpdate(BaseModel):
    code: Optional[str] = None
    category: Optional[str] = None
    text: Optional[str] = None
    severity_default: Optional[str] = None
    channels: Optional[List[str]] = None
    examples_good: Optional[List[str]] = None
    examples_bad: Optional[List[str]] = None
    source_doc: Optional[str] = None

class RuleResponse(RuleBase):
    id: int
    kb_version_id: int

    class Config:
        from_attributes = True

class FactBase(BaseModel):
    code: str
    key: str
    value: str
    unit: Optional[str] = None
    source: Optional[str] = None
    owner: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None

class FactCreate(FactBase):
    pass

class FactUpdate(BaseModel):
    code: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    owner: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None

class FactResponse(FactBase):
    id: int
    kb_version_id: int
    is_stale: bool = False

    class Config:
        from_attributes = True

class TermBase(BaseModel):
    preferred: str
    banned: Optional[List[str]] = None
    case_rule: Optional[str] = None
    notes: Optional[str] = None

class TermCreate(TermBase):
    pass

class TermUpdate(BaseModel):
    preferred: Optional[str] = None
    banned: Optional[List[str]] = None
    case_rule: Optional[str] = None
    notes: Optional[str] = None

class TermResponse(TermBase):
    id: int
    kb_version_id: int

    class Config:
        from_attributes = True

class ClaimBase(BaseModel):
    approved_text: str
    evidence_ref: Optional[str] = None
    required_disclaimer: Optional[str] = None
    valid_to: Optional[datetime] = None

class ClaimCreate(ClaimBase):
    pass

class ClaimUpdate(BaseModel):
    approved_text: Optional[str] = None
    evidence_ref: Optional[str] = None
    required_disclaimer: Optional[str] = None
    valid_to: Optional[datetime] = None

class ClaimResponse(ClaimBase):
    id: int
    kb_version_id: int
    is_expired: bool = False

    class Config:
        from_attributes = True

class AssetBase(BaseModel):
    type: str  # logo | palette | font | template
    spec_json: Optional[Dict[str, Any]] = None
    file_ref: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetResponse(AssetBase):
    id: int
    kb_version_id: int

    class Config:
        from_attributes = True

class KBVersionResponse(BaseModel):
    id: int
    workspace_id: int
    label: str
    is_active: bool
    created_at: datetime
    created_by: Optional[int] = None
    rules_count: int = 0
    facts_count: int = 0
    terms_count: int = 0
    claims_count: int = 0
    assets_count: int = 0

    class Config:
        from_attributes = True
