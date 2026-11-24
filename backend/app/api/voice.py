"""Authenticated bounded voice sessions; credentials never go to browser or URL."""
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket
from sqlalchemy import select
from app.config import settings
from app.db import SessionLocal
from app.models import AuthSession, User
from app.security import COOKIE,digest

router=APIRouter(prefix='/voice',tags=['voice'])
active_sessions=set()

@router.get('/status')
def voice_status():
    enabled=bool(settings.voice_enabled and settings.deepgram_api_key)
    return {'enabled':enabled,'provider':'pipecat-deepgram','requires_login':True,
            'max_seconds':min(max(settings.voice_max_seconds,1),120),
            'message':'点击后麦克风音频传给语音服务，仅转写不自动发送需求' if enabled else '语音未配置：需要VOICE_ENABLED与DEEPGRAM_API_KEY'}

@router.websocket('/ws')
async def transcription(websocket:WebSocket):
    if websocket.headers.get('origin')!=settings.public_origin:
        await websocket.close(code=1008);return
    token=websocket.cookies.get(COOKIE,'')
    with SessionLocal() as db:
        auth=db.get(AuthSession,digest(token)) if token else None
        if not auth or auth.expires_at<=datetime.now(timezone.utc) or (auth.mock and (settings.production or not settings.dev_mock_auth)):
            await websocket.close(code=1008);return
        user=db.get(User,auth.user_id)
        if not user or (settings.production and user.email.endswith('@mock.invalid')):
            await websocket.close(code=1008);return
        owner=user.id
    if not settings.voice_enabled or not settings.deepgram_api_key:
        await websocket.close(code=1013);return
    if owner in active_sessions or len(active_sessions)>=min(max(settings.voice_max_connections,1),4):
        await websocket.close(code=1013);return
    active_sessions.add(owner)
    try:
        from app.services.voice import run_transcription
        await websocket.accept()
        await run_transcription(websocket)
    except Exception:
        # Never return SDK errors: they may include secrets or private transcripts.
        try:await websocket.send_json({'type':'error','message':'语音连接中断，请手动重试'})
        except Exception:pass
    finally:
        active_sessions.discard(owner)
        try:await websocket.close()
        except Exception:pass
