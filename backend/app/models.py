import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

def uid():
    return str(uuid.uuid4())

def now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class OAuthIdentity(Base):
    __tablename__ = 'oauth_identities'
    __table_args__ = (UniqueConstraint('provider', 'subject', name='uq_oauth_provider_subject'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    provider: Mapped[str] = mapped_column(String(20))
    subject: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class OAuthChallenge(Base):
    __tablename__ = 'oauth_challenges'
    state_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    nonce_hash: Mapped[str] = mapped_column(String(64))
    browser_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class Workspace(Base):
    __tablename__ = 'workspaces'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True)
    name: Mapped[str] = mapped_column(String(60), default='个人工作区')

class LoginChallenge(Base):
    __tablename__ = 'login_challenges'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class AuthSession(Base):
    __tablename__ = 'auth_sessions'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    mock: Mapped[bool] = mapped_column(default=False,server_default='false')
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class RateLimit(Base):
    __tablename__ = 'rate_limits'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    count: Mapped[int] = mapped_column(Integer, default=0)

class Project(Base):
    __tablename__ = 'projects'
    __table_args__ = (UniqueConstraint('owner_id', 'idempotency_key', name='uq_project_idempotency'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'))
    idempotency_key: Mapped[str] = mapped_column(String(36))
    name: Mapped[str] = mapped_column(String(60))
    initial_prompt: Mapped[str] = mapped_column(Text)
    current_build_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Message(Base):
    __tablename__ = 'messages'
    __table_args__ = (UniqueConstraint('project_id', 'idempotency_key', name='uq_message_idempotency'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id'), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(36))
    role: Mapped[str] = mapped_column(String(20), default='user')
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class ModelConfiguration(Base):
    __tablename__ = 'model_configurations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True)
    provider: Mapped[str] = mapped_column(String(40))
    base_url: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(128))
    version: Mapped[int] = mapped_column(Integer, default=1)
    ciphertext: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class ModelDraft(Base):
    __tablename__ = 'model_drafts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(36))
    provider: Mapped[str] = mapped_column(String(40))
    base_url: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(128))
    ciphertext: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default='testing')
    error: Mapped[str | None] = mapped_column(Text)
    config_version: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint('owner_id', 'idempotency_key', name='uq_model_test_idempotency'),)

class GenerationRun(Base):
    __tablename__ = 'generation_runs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id'), index=True)
    message_id: Mapped[str] = mapped_column(ForeignKey('messages.id'))
    base_build_id: Mapped[str | None] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(20), default='queued')
    provider: Mapped[str] = mapped_column(String(60))
    model: Mapped[str] = mapped_column(String(128))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config_id: Mapped[str | None] = mapped_column(ForeignKey('model_configurations.id'))
    config_version: Mapped[int | None] = mapped_column(Integer)
    idempotency_key: Mapped[str | None] = mapped_column(String(36))
    retry_of: Mapped[str | None] = mapped_column(String(36))
    worker_token: Mapped[str | None] = mapped_column(String(36))
    events: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text)
    candidate: Mapped[dict | None] = mapped_column(JSON)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint('project_id', 'idempotency_key', name='uq_run_idempotency'),)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class BuildArtifact(Base):
    __tablename__ = 'build_artifacts'
    __table_args__ = (UniqueConstraint('project_id', 'number', name='uq_build_number'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id'), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey('generation_runs.id'))
    number: Mapped[int] = mapped_column(Integer)
    artifact: Mapped[dict] = mapped_column(JSON)
    validation: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Publication(Base):
    __tablename__ = 'publications'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id'), unique=True)
    published_build_id: Mapped[str | None] = mapped_column(ForeignKey('build_artifacts.id'))
    status: Mapped[str] = mapped_column(String(20), default='unpublished')
    public_url: Mapped[str | None] = mapped_column(Text)
    target_build_id: Mapped[str | None] = mapped_column(String(36))
    job_key: Mapped[str | None] = mapped_column(String(36))
    error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
