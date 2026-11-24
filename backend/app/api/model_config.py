import asyncio
from datetime import timedelta, timezone
from uuid import UUID
from urllib.parse import urlsplit
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.auth import StrictInput
from app.config import settings
from app.db import get_db
from app.models import ModelConfiguration, ModelDraft, GenerationRun, User, now, uid
from app.security import current_user, advisory_lock
from app.services.credentials import encrypt, decrypt, CredentialError
from app.services.provider import completion, resolve_target, ProviderError

router=APIRouter(prefix='/model-config',tags=['model configuration'])
ACTIVE=('queued','planning','generating','validating','cancelling')

class TestConfiguration(StrictInput):
    provider: str = Field(pattern=r'^(openai|deepseek|custom|mock)$')
    api_key: str = Field('',max_length=4096)
    base_url: str = Field(max_length=1024)
    model: str = Field(min_length=1,max_length=128)
    idempotency_key: UUID
    consent: bool

class SaveConfiguration(StrictInput):
    draft_id: UUID
    consent: bool

class DeleteConfiguration(StrictInput):
    confirm: bool

def status_view(config):
    if not config or not config.enabled or config.deleted_at:
        return None
    return {'id':config.id,'provider':config.provider,'base_url':config.base_url,'model':config.model,
            'version':config.version,'enabled':config.enabled,'tested_at':config.tested_at.astimezone(timezone.utc),
            'key_status':'已加密保存，不可回显','mock':config.provider=='mock'}

def enabled_config(db,user,config_id=None,version=None):
    config=db.scalar(select(ModelConfiguration).where(ModelConfiguration.owner_id==user.id))
    if not config or not config.enabled or config.deleted_at or not config.ciphertext:
        raise HTTPException(428,'请先完成服务端模型测试与加密保存')
    if config_id is not None and (str(config_id)!=config.id or version!=config.version):
        raise HTTPException(409,'配置版本已变化，请刷新')
    if config.provider=='mock' and (settings.production or not settings.dev_mock_model):
        raise HTTPException(428,'开发Mock已禁用，请配置真实模型')
    return config

def config_not_running(db,user):
    active=db.scalar(select(GenerationRun).join(ModelConfiguration,GenerationRun.config_id==ModelConfiguration.id).where(ModelConfiguration.owner_id==user.id,GenerationRun.status.in_(ACTIVE)))
    if active:raise HTTPException(409,'活动任务期间不能更换配置；请先停止或等待完成')

@router.get('')
def get_config(user:User=Depends(current_user),db:Session=Depends(get_db)):
    config=db.scalar(select(ModelConfiguration).where(ModelConfiguration.owner_id==user.id))
    view=status_view(config)
    if view and config.provider=='mock' and not settings.dev_mock_model:view=None
    return {'config':view}

@router.post('/test')
async def test(body:TestConfiguration,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not body.consent:raise HTTPException(422,'请确认测试费用与数据传输')
    advisory_lock(db,'model:'+user.id);config_not_running(db,user)
    previous=db.scalar(select(ModelDraft).where(ModelDraft.owner_id==user.id,ModelDraft.idempotency_key==str(body.idempotency_key)))
    if previous:
        if (previous.provider,previous.base_url,previous.model)!=(body.provider,body.base_url,body.model):raise HTTPException(409,'幂等键已用于不同测试')
        if previous.expires_at<=now():raise HTTPException(409,'测试结果过期，请发起新测试')
        if body.api_key and previous.ciphertext and body.api_key!=decrypt(previous.ciphertext,user.id,previous.id,'draft'):raise HTTPException(409,'幂等键已用于不同凭证测试')
        return {'draft_id':previous.id,'status':previous.status,'error':previous.error,'expires_at':previous.expires_at}
    existing=db.scalar(select(ModelConfiguration).where(ModelConfiguration.owner_id==user.id))
    running=db.scalar(select(ModelDraft).where(ModelDraft.owner_id==user.id,ModelDraft.status=='testing',ModelDraft.expires_at>now()))
    if running:raise HTTPException(409,'已有连接测试进行中')
    if body.provider=='mock':
        if settings.production or not settings.dev_mock_model:raise HTTPException(422,'Mock模型已禁用')
        if body.base_url!='mock://local':raise HTTPException(422,'Mock仅支持本地fixture')
        key='MOCK-NON-SECRET'
    else:
        if body.provider=='openai' and urlsplit(body.base_url).netloc!='api.openai.com':raise HTTPException(422,'OpenAI预设目标不匹配')
        if body.provider=='deepseek' and urlsplit(body.base_url).netloc!='api.deepseek.com':raise HTTPException(422,'DeepSeek预设目标不匹配')
        await asyncio.to_thread(resolve_target,body.base_url)
        key=body.api_key
        if not key:
            if not existing or not existing.ciphertext or existing.deleted_at or existing.base_url!=body.base_url or existing.provider!=body.provider:
                raise HTTPException(422,'新配置或更换供应商需要输入新Key')
            key=decrypt(existing.ciphertext,user.id,existing.id,existing.version)
    draft=ModelDraft(id=uid(),owner_id=user.id,idempotency_key=str(body.idempotency_key),provider=body.provider,base_url=body.base_url,model=body.model,config_version=existing.version if existing else 0,expires_at=now()+timedelta(minutes=15))
    draft.ciphertext=encrypt(key,user.id,draft.id,'draft');db.add(draft);db.commit()
    try:
        if body.provider=='mock':await asyncio.sleep(0.15)
        else:await completion(draft,key,[{'role':'user','content':'Reply with OK only.'}],timeout=15,max_tokens=8)
        draft.status='passed'
    except ProviderError as exc:
        draft.status='failed';draft.error=str(exc);draft.ciphertext=None
    finally:
        key=''
    db.commit()
    return {'draft_id':draft.id,'status':draft.status,'error':draft.error,'expires_at':draft.expires_at,'mock':draft.provider=='mock'}

@router.post('/save')
def save(body:SaveConfiguration,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not body.consent:raise HTTPException(422,'需同意服务端加密保存及费用规则')
    advisory_lock(db,'model:'+user.id);config_not_running(db,user)
    draft=db.scalar(select(ModelDraft).where(ModelDraft.id==str(body.draft_id),ModelDraft.owner_id==user.id).with_for_update())
    if not draft or draft.status!='passed' or draft.expires_at<=now() or not draft.ciphertext:raise HTTPException(409,'测试草稿无效或过期，请重测')
    config=db.scalar(select(ModelConfiguration).where(ModelConfiguration.owner_id==user.id))
    if (config.version if config else 0)!=draft.config_version:raise HTTPException(409,'配置版本冲突，请重新测试')
    if draft.provider=='mock' and (settings.production or not settings.dev_mock_model):raise HTTPException(422,'Mock模型已禁用')
    if not config:
        config=ModelConfiguration(id=uid(),owner_id=user.id,provider=draft.provider,base_url=draft.base_url,model=draft.model,version=0);db.add(config)
    config.version+=1
    key=decrypt(draft.ciphertext,user.id,draft.id,'draft')
    config.ciphertext=encrypt(key,user.id,config.id,config.version);key=''
    config.provider,config.base_url,config.model=draft.provider,draft.base_url,draft.model
    config.enabled=True;config.deleted_at=None;config.tested_at=now()
    draft.status='saved';draft.ciphertext=None;db.commit()
    return {'config':status_view(config)}

@router.post('/delete')
def delete(body:DeleteConfiguration,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not body.confirm:raise HTTPException(422,'需确认删除并停止相关任务')
    advisory_lock(db,'model:'+user.id)
    config=db.scalar(select(ModelConfiguration).where(ModelConfiguration.owner_id==user.id).with_for_update())
    if config:
        config.enabled=False;config.deleted_at=now();config.ciphertext=None;config.version+=1
        for run in db.scalars(select(GenerationRun).where(GenerationRun.config_id==config.id,GenerationRun.status.in_(ACTIVE)).with_for_update()):
            run.status='cancelled';run.error='配置已删除，任务已取消';run.finished_at=now();run.candidate=None
    for draft in db.scalars(select(ModelDraft).where(ModelDraft.owner_id==user.id)):
        draft.ciphertext=None;draft.status='deleted'
    db.commit()
    return {'config':None}
