"""Readiness is observed, not inferred from a successful deployment or saved key."""
from datetime import timedelta
from urllib.parse import urlsplit
from sqlalchemy import select
from fastapi import HTTPException
from app.config import settings
from app.db import SessionLocal
from app.models import ServiceHeartbeat, now


def heartbeat(service_id, role, mock_only=False):
    with SessionLocal() as db:
        row = db.get(ServiceHeartbeat, service_id)
        if not row:
            row = ServiceHeartbeat(id=service_id, role=role, mock_only=mock_only, seen_at=now())
            db.add(row)
        row.seen_at = now()
        db.commit()


def readiness(db, provider):
    cutoff = now() - timedelta(seconds=20)
    workers = db.scalars(select(ServiceHeartbeat).where(
        ServiceHeartbeat.role == 'worker', ServiceHeartbeat.seen_at > cutoff)).all()
    ready = any(not row.mock_only or provider == 'mock' for row in workers)
    application = db.scalar(select(ServiceHeartbeat).where(
        ServiceHeartbeat.role == 'application', ServiceHeartbeat.seen_at > cutoff)) is not None
    publication = db.scalar(select(ServiceHeartbeat).where(
        ServiceHeartbeat.role == 'publication', ServiceHeartbeat.seen_at > cutoff)) is not None
    def isolated(origin):
        target,platform=urlsplit(origin),urlsplit(settings.public_origin)
        public_https=platform.scheme=='https'
        if public_https and target.scheme!='https':return False
        return (target.scheme,target.hostname,target.port)!=(platform.scheme,platform.hostname,platform.port)
    preview = application and isolated(settings.preview_origin)
    publish = publication and isolated(settings.app_origin)
    if settings.application_sandbox:
        preview = publish = True
    if provider == 'mock' and settings.dev_mock_sandbox and not settings.production:
        preview = publish = True
    return {'worker_ready': ready, 'preview_ready': preview, 'publication_ready':publish,
            'can_generate': ready,
            'reason': '' if ready else '生成服务未就绪，需求已保留；服务恢复后请手动提交'}


def require_worker(db, provider):
    state = readiness(db, provider)
    if not state['can_generate']:
        raise HTTPException(503, state['reason'])
