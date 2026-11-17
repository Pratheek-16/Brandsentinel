"""SQLAlchemy models for BrandSentinel.
Only a subset needed for initial runnable prototype.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
import enum
import datetime

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

class KBVersion(Base):
    __tablename__ = "kb_versions"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    label = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    workspace = relationship("Workspace", back_populates="kb_versions")

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
    creator = relationship("User")
    versions = relationship("ContentVersion", back_populates="content")

class ContentVersion(Base):
    __tablename__ = "content_versions"
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    text_body = Column(Text, nullable=True)
    file_ref = Column(String, nullable=True)
    content_hash = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    content = relationship("Content", back_populates="versions")

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
