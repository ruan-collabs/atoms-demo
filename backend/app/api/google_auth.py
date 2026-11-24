import base64
import hashlib
import hmac
import secrets
from datetime import timedelta
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from app.api.auth import StrictInput, limit_ip, issue_session
from app.config import settings
from app.db import get_db
from app.models import OAuthChallenge, OAuthIdentity, User, Workspace, now, uid
from app.security import advisory_lock, digest
from app.services import google

router = APIRouter(prefix='/auth/google', tags=['google-auth'])
OAUTH_COOKIE = 'atoms_oauth_verifier'

class StartGoogle(StrictInput):
    terms_accepted: bool

@router.post('/start')
def start(body: StartGoogle, request: Request, response: Response, db: Session = Depends(get_db)):
    if not settings.google_enabled:
        raise HTTPException(503, 'Google登录尚未配置，请配置OAuth Client ID与Secret')
    if not body.terms_accepted:
        raise HTTPException(422, '请先同意演示条款')
    limit_ip(db, request.client.host if request.client else 'unknown')
    state, nonce, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    challenge = OAuthChallenge(state_hash=digest(state), nonce_hash=digest(nonce), browser_hash=digest(state+':'+verifier), expires_at=now()+timedelta(minutes=10))
    db.add(challenge);db.commit()
    response.set_cookie(OAUTH_COOKIE, verifier, httponly=True, secure=settings.production, samesite='lax', max_age=600, path='/api/auth/google')
    pkce = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    return {'authorization_url':google.AUTHORIZATION_URL+'?'+urlencode({
        'client_id':settings.google_client_id,'redirect_uri':settings.google_redirect_uri,
        'response_type':'code','scope':'openid email','state':state,'nonce':nonce,
        'code_challenge':pkce,'code_challenge_method':'S256','prompt':'select_account',
    })}

def finish(location):
    response=RedirectResponse(settings.public_origin+location,status_code=303)
    response.delete_cookie(OAUTH_COOKIE,path='/api/auth/google',secure=settings.production,httponly=True,samesite='lax')
    return response

@router.get('/callback')
async def callback(request: Request, state: str = Query('', max_length=128), code: str = Query('', max_length=4096), error: str = Query('', max_length=128), db: Session = Depends(get_db)):
    if not settings.google_enabled:
        return finish('/login?auth_error=google_not_configured')
    verifier=request.cookies.get(OAUTH_COOKIE,'')
    challenge=db.scalar(select(OAuthChallenge).where(OAuthChallenge.state_hash==digest(state)).with_for_update()) if state else None
    if not challenge or challenge.consumed_at or challenge.expires_at <= now() or not verifier or not hmac.compare_digest(challenge.browser_hash,digest(state+':'+verifier)):
        db.rollback()
        return finish('/login?auth_error=invalid_state')
    # Consume state before network calls so replay/concurrent callbacks cannot log in twice.
    nonce_hash=challenge.nonce_hash
    challenge.consumed_at=now();db.commit()
    if error:
        return finish('/login?auth_error=google_cancelled')
    if not code:
        return finish('/login?auth_error=google_failed')
    try:
        token=await google.exchange_code(code,verifier)
        identity=await run_in_threadpool(google.validate_id_token,token,nonce_hash)
    except google.GoogleAuthError:
        return finish('/login?auth_error=google_failed')
    advisory_lock(db,'google-sub:'+identity['sub'])
    linked=db.scalar(select(OAuthIdentity).where(OAuthIdentity.provider=='google',OAuthIdentity.subject==identity['sub']))
    if linked:
        user=db.get(User,linked.user_id)
    else:
        advisory_lock(db,'user:'+identity['email'])
        existing=db.scalar(select(User).where(User.email==identity['email']))
        if existing:
            # Email matching is not proof of account ownership: never auto-merge.
            db.rollback()
            return finish('/login?auth_error=account_exists')
        user=User(id=uid(),email=identity['email'])
        db.add(user);db.flush()
        db.add(Workspace(owner_id=user.id))
        db.add(OAuthIdentity(user_id=user.id,provider='google',subject=identity['sub']))
    response=finish('/dashboard')
    issue_session(db,user,response)
    db.commit()
    return response
