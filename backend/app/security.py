import hashlib
import hmac
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.config import settings
from app.db import get_db
from app.models import AuthSession, User

COOKIE = 'atoms_session'

def digest(value: str) -> str:
    return hmac.new(settings.app_secret.encode(), value.encode(), hashlib.sha256).hexdigest()

def advisory_lock(db: Session, value: str):
    key = int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], 'big', signed=True)
    db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': key})

def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE, '')
    auth = db.get(AuthSession, digest(token)) if token else None
    if not auth or (auth.mock and (settings.production or not settings.dev_mock_auth)) or auth.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(401, '登录已失效，请重新登录')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        csrf = request.headers.get('X-CSRF-Token', '')
        if not csrf or not hmac.compare_digest(digest(csrf), auth.csrf_hash):
            raise HTTPException(403, '安全校验失败，请刷新后重试')
    user=db.scalar(select(User).where(User.id==auth.user_id))
    if settings.production and user.email.endswith('@mock.invalid'):
        raise HTTPException(401,'开发测试身份不能用于生产')
    return user
