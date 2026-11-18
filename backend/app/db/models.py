"""SQLAlchemy models for BrandSentinel.
All tables required by the specification are defined here.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship, declarative_base
import enum
import datetime
import hashlib

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    creator = "creator"
    manager = "manager"
    reviewer = "reviewer"
    admin = "admin"

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    confidential_tier = Column(String, default="low")
    ai_mode = Column(String, default="cloud")
    retention_days = Column(Integer, default=30)
    users = relationship("User", back_populates="workspace")
    kb_versions = relationship("KBVersion", back_populates="workspace")
    risk_rules = relationship("RiskRule", back_populates="workspace")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    role = Column(Enum(RoleEnum), nullable=False)
    password_hash = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    workspace = relationship("Workspace", back_populates="users")
    created_contents = relationship("Content", back_populates="creator")

class KBVersion(Base):
    __tablename__ = "kb_versions"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    label = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    workspace = relationship("Workspace", back_populates="kb_versions")
    rules = relationship("Rule", back_populates="kb_version")
    facts = relationship("Fact", back_populates="kb_version")
    terms = relationship("Term", back_populates="kb_version")
    claims = relationship("Claim", back_populates="kb_version")
    assets = relationship("Asset", back_populates="kb_version")

# Section 5 tables
class Rule(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, index=True)
    kb_version_id = Column(Integer, ForeignKey("kb_versions.id"), nullable=False)
    code = Column(String, nullable=False)
    category = Column(String, nullable=False)  # tone|terminology|messaging|visual|accessibility|claim
    text = Column(Text, nullable=False)
    severity_default = Column(String, nullable=False)
    channels = Column(JSON, nullable=True)
    examples_good = Column(JSON, nullable=True)
    examples_bad = Column(JSON, nullable=True)
    source_doc = Column(String, nullable=True)
    embedding = Column(JSON, nullable=True)
    kb_version = relationship("KBVersion", back_populates="rules")

class Fact(Base):
    __tablename__ = "facts"
    id = Column(Integer, primary_key=True, index=True)
    kb_version_id = Column(Integer, ForeignKey("kb_versions.id"), nullable=False)
    code = Column(String, nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    unit = Column(String, nullable=True)
    source = Column(String, nullable=True)
    owner = Column(String, nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    embedding = Column(JSON, nullable=True)
    kb_version = relationship("KBVersion", back_populates="facts")

class Term(Base):
    __tablename__ = "terms"
    id = Column(Integer, primary_key=True, index=True)
    kb_version_id = Column(Integer, ForeignKey("kb_versions.id"), nullable=False)
    preferred = Column(String, nullable=False)
    banned = Column(JSON, nullable=True)  # list of banned variants
    case_rule = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    kb_version = relationship("KBVersion", back_populates="terms")

class Claim(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True, index=True)
    kb_version_id = Column(Integer, ForeignKey("kb_versions.id"), nullable=False)
    approved_text = Column(Text, nullable=False)
    evidence_ref = Column(String, nullable=True)
    required_disclaimer = Column(String, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    kb_version = relationship("KBVersion", back_populates="claims")

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    kb_version_id = Column(Integer, ForeignKey("kb_versions.id"), nullable=False)
    type = Column(String, nullable=False)  # logo|palette|font|template
    spec_json = Column(JSON, nullable=True)
    file_ref = Column(String, nullable=True)
    kb_version = relationship("KBVersion", back_populates="assets")

class RiskRule(Base):
    __tablename__ = "risk_rules"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    condition_json = Column(JSON, nullable=False)
    route_to = Column(String, nullable=False)  # manager|reviewer
    description = Column(Text, nullable=True)
    workspace = relationship("Workspace", back_populates="risk_rules")

class Content(Base):
    __tablename__ = "contents"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)  # text, docx, pdf, image
    channel = Column(String, nullable=True)
    status = Column(String, default="draft")
    current_version_id = Column(Integer, ForeignKey("content_versions.id"), nullable=True)
    workspace = relationship("Workspace")
    creator = relationship("User", back_populates="created_contents")
    versions = relationship("ContentVersion", back_populates="content", foreign_keys="ContentVersion.content_id")

class ContentVersion(Base):
    __tablename__ = "content_versions"
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    text_body = Column(Text, nullable=True)
    file_ref = Column(String, nullable=True)
    content_hash = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    content = relationship("Content", back_populates="versions", foreign_keys=[content_id])

class ReviewRun(Base):
    __tablename__ = "review_runs"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("content_versions.id"), nullable=False)
    kb_version_id = Column(Integer, ForeignKey("kb_versions.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    provider = Column(String, default="mock")
    model = Column(String, default="mock")
    status = Column(String, default="pending")

class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, index=True)
    review_run_id = Column(Integer, ForeignKey("review_runs.id"), nullable=False)
    category = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    confidence = Column(String, nullable=False)
    span_start = Column(Integer, nullable=False)
    span_end = Column(Integer, nullable=False)
    span_text = Column(Text, nullable=False)
    evidence_type = Column(String, nullable=True)
    evidence_id = Column(String, nullable=True)
    evidence_quote = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)
    suggestion_text = Column(Text, nullable=True)
    claim_status = Column(String, default="n/a")
    status = Column(String, default="open", nullable=False)  # open | accepted | edited | dismissed
    selected_replacement = Column(Text, nullable=True)
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    dismissal_reason = Column(Text, nullable=True)

class AIUsage(Base):
    __tablename__ = "ai_usages"
    id = Column(Integer, primary_key=True, index=True)
    review_run_id = Column(Integer, ForeignKey("review_runs.id"), nullable=False)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    purpose = Column(String, nullable=False)  # e.g., "redaction", "review"
    segments_sent = Column(Integer, nullable=False, default=0)
    segments_received = Column(Integer, nullable=False, default=0)
    redacted_fields = Column(JSON, nullable=True)
    redaction_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("content_versions.id"), nullable=False)
    finding_id = Column(Integer, ForeignKey("findings.id"), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("content_versions.id"), nullable=False)
    role = Column(String, nullable=False)
    decision = Column(String, nullable=False)  # approved|changes_requested|rejected|escalated
    reason = Column(Text, nullable=True)
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    decided_at = Column(DateTime, default=datetime.datetime.utcnow)
    signature_hash = Column(String, nullable=False)

# Deprecated duplicate AIUsage model removed; using the earlier definition with __tablename__ = "ai_usages"

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    payload_json = Column(JSON, nullable=True)
    prev_hash = Column(String, nullable=True)
    hash = Column(String, nullable=False)
    ts = Column(DateTime, default=datetime.datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    payload_json = Column(JSON, nullable=True)
    status = Column(String, nullable=False)
    attempts = Column(Integer, default=0)
    result_json = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
