import secrets
from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import settings
from app.db import get_db
from app.models import AuthSession, LoginChallenge, RateLimit, User, Workspace, now, uid
from app.security import COOKIE, advisory_lock, current_user, digest
from app.services.mail import MailUnavailable, send_code

router = APIRouter(prefix='/auth', tags=['auth'])

class StrictInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class SendCode(StrictInput):
    email: EmailStr = Field(max_length=254)
    terms_accepted: bool

class VerifyCode(StrictInput):
    challenge_id: UUID
    code: str = Field(pattern=r'^\d{6}$')

def challenge_info(challenge: LoginChallenge):
    local, domain = challenge.email.split('@')
    return {'challenge_id': challenge.id, 'masked_email': local[:2] + '***@' + domain,
            'expires_at': challenge.expires_at, 'resend_after': challenge.created_at + timedelta(seconds=60)}

def limit_ip(db, ip):
    key = digest('otp-ip:' + ip)
    advisory_lock(db, key)
    row = db.get(RateLimit, key)
    timestamp = now()
    if row is None:
        row = RateLimit(key=key, window_start=timestamp, count=0)
        db.add(row)
    if row.window_start + timedelta(minutes=15) < timestamp:
        row.window_start, row.count = timestamp, 0
    if row.count >= 20:
        raise HTTPException(429, '请求过于频繁，请稍后重试')
    row.count += 1

@router.post('/email/code', status_code=202)
def request_code(body: SendCode, request: Request, db: Session = Depends(get_db)):
    if not body.terms_accepted:
        raise HTTPException(422, '请先同意演示条款')
    email = str(body.email).lower()
    limit_ip(db, request.client.host if request.client else 'unknown')
    advisory_lock(db, 'email:' + email)
    latest = db.scalar(select(LoginChallenge).where(LoginChallenge.email == email).order_by(LoginChallenge.created_at.desc()).limit(1))
    timestamp = now()
    if latest and latest.blocked_until and latest.blocked_until > timestamp:
        db.commit()
        raise HTTPException(429, '验证已暂停，请15分钟后重试')
    if latest and latest.created_at + timedelta(seconds=60) > timestamp:
        db.commit()
        raise HTTPException(429, '请等待60秒后重新发送')
    code = f'{secrets.randbelow(1000000):06d}'
    challenge = LoginChallenge(id=uid(), email=email, code_hash='', created_at=timestamp, expires_at=timestamp + timedelta(minutes=10))
    challenge.code_hash = digest(challenge.id + ':' + code)
    db.add(challenge)
    try:
        send_code(email, code)
    except MailUnavailable as exc:
        db.rollback()
        raise HTTPException(503, str(exc)) from None
    if latest:
        latest.consumed_at = timestamp
    db.commit()
    return challenge_info(challenge)

@router.get('/challenges/{challenge_id}')
def get_challenge(challenge_id: UUID, db: Session = Depends(get_db)):
    challenge = db.get(LoginChallenge, str(challenge_id))
    if not challenge or challenge.consumed_at or challenge.expires_at <= now():
        raise HTTPException(410, '验证码已过期，请重新发送')
    return challenge_info(challenge)

def issue_session(db: Session, user: User, response: Response):
    token = secrets.token_urlsafe(32)
    csrf = digest('csrf:' + token)
    db.add(AuthSession(id=digest(token), user_id=user.id, csrf_hash=digest(csrf), expires_at=now() + timedelta(days=settings.session_days)))
    response.set_cookie(COOKIE, token, max_age=settings.session_days * 86400, httponly=True, secure=settings.secure_cookies, samesite='lax', path='/')
    return csrf

@router.post('/email/verify')
def verify(body: VerifyCode, response: Response, db: Session = Depends(get_db)):
    challenge = db.scalar(select(LoginChallenge).where(LoginChallenge.id == str(body.challenge_id)).with_for_update())
    timestamp = now()
    if not challenge or challenge.consumed_at:
        raise HTTPException(400, '验证码无效或已使用')
    if challenge.blocked_until and challenge.blocked_until > timestamp:
        raise HTTPException(429, '验证已暂停，请15分钟后重试')
    if challenge.expires_at <= timestamp:
        raise HTTPException(410, '验证码已过期，请重新发送')
    import hmac
    if not hmac.compare_digest(challenge.code_hash, digest(challenge.id + ':' + body.code)):
        challenge.attempts += 1
        if challenge.attempts >= 5:
            challenge.blocked_until = timestamp + timedelta(minutes=15)
        db.commit()
        raise HTTPException(429 if challenge.attempts >= 5 else 400, '验证已暂停，请15分钟后重试' if challenge.attempts >= 5 else '验证码不正确')
    advisory_lock(db, 'user:' + challenge.email)
    user = db.scalar(select(User).where(User.email == challenge.email))
    if not user:
        user = User(id=uid(), email=challenge.email)
        db.add(user)
        db.flush()
        db.add(Workspace(owner_id=user.id))
    challenge.consumed_at = timestamp
    csrf = issue_session(db, user, response)
    db.commit()
    return {'user': {'id': user.id, 'email': user.email}, 'csrf_token': csrf}

@router.get('/me')
def me(user: User = Depends(current_user)):
    return {'id': user.id, 'email': user.email}

@router.get('/csrf')
def csrf_token(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    # Stable session-bound token: refreshing another tab must not invalidate this tab.
    token = digest('csrf:' + request.cookies[COOKIE])
    return {'csrf_token': token}

@router.post('/logout', status_code=204)
def logout(request: Request, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    auth = db.get(AuthSession, digest(request.cookies[COOKIE]))
    db.delete(auth)
    db.commit()
    response.delete_cookie(COOKIE, path='/', secure=settings.secure_cookies, httponly=True, samesite='lax')
