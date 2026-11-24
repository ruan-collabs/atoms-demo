from datetime import timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.auth import StrictInput
from app.api.projects import owned, message_view
from app.api.model_config import ACTIVE, enabled_config
from app.config import settings
from app.db import get_db
from app.models import GenerationRun, BuildArtifact, Message, User, now, uid
from app.security import advisory_lock, current_user
from app.worker import add_event, commit_candidate, JobStopped
from app.services.readiness import readiness, require_worker

router=APIRouter(prefix='/projects',tags=['generation'])
class Generate(StrictInput):
    prompt: str = Field(min_length=1,max_length=4000)
    idempotency_key: UUID
    config_id: UUID
    config_version: int
    base_build_id: UUID | None = None
    message_id: UUID | None = None

class Retry(StrictInput):
    idempotency_key: UUID
    config_id: UUID
    config_version: int


def run_view(run):
    if not run:return None
    return {'id':run.id,'status':run.status,'error':run.error,'events':run.events,'retry_of':run.retry_of,'created_at':run.created_at.astimezone(timezone.utc),'finished_at':run.finished_at.astimezone(timezone.utc) if run.finished_at else None,'mock':run.provider=='mock', 'requires_resubmit':run.status=='queued' and run.provider!='mock' and run.dispatch_version!=1,'stream_bytes':run.stream_bytes or 0}

@router.get('/generation/service-status')
def service_status(user:User=Depends(current_user),db:Session=Depends(get_db)):
    config=enabled_config(db,user)
    return readiness(db,config.provider)

@router.get('/{project_id}/runs/{run_id}/stream')
def stream_snapshot(project_id:UUID,run_id:UUID,offset:int=Query(0,ge=0),revision:int=Query(0,ge=0),user:User=Depends(current_user),db:Session=Depends(get_db)):
    owned(db,project_id,user)
    run=db.scalar(select(GenerationRun).where(GenerationRun.id==str(run_id),GenerationRun.project_id==str(project_id)))
    if not run:raise HTTPException(404,'任务不可访问')
    text=run.stream_text or ''
    # A repair may reset output. Offset is a Unicode character offset, not bytes.
    reset=offset>len(text) or revision!=run.stream_revision
    if reset:offset=0
    end=min(len(text),offset+32768)
    return {'run_id':run.id,'offset':offset,'next_offset':end,'delta':text[offset:end], 'reset':reset,'revision':run.stream_revision,'stream_bytes':run.stream_bytes or 0,'status':run.status}

def enqueue(db,project,config,message,key,retry_of=None):
    active=db.scalar(select(GenerationRun).where(GenerationRun.project_id==project.id,GenerationRun.status.in_(ACTIVE)))
    if active:raise HTTPException(409,'当前只允许一个生成任务')
    require_worker(db,config.provider)
    run=GenerationRun(id=uid(),project_id=project.id,message_id=message.id,base_build_id=project.current_build_id,provider=config.provider,model=config.model,config_id=config.id,config_version=config.version,idempotency_key=key,retry_of=retry_of)
    add_event(run,'queued','任务已被服务器接受'+(' [开发Mock]' if config.provider=='mock' else ''))
    db.add(run);project.updated_at=now();return run

@router.post('/{project_id}/generate',status_code=202)
def generate(project_id:UUID,body:Generate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=owned(db,project_id,user)
    advisory_lock(db,'model:'+user.id);advisory_lock(db,'generation:'+project.id)
    existing=db.scalar(select(GenerationRun).where(GenerationRun.project_id==project.id,GenerationRun.idempotency_key==str(body.idempotency_key)))
    if existing:
        if db.get(Message,existing.message_id).content!=body.prompt:raise HTTPException(409,'幂等键已用于不同需求')
        return run_view(existing)
    config=enabled_config(db,user,body.config_id,body.config_version)
    if project.current_build_id!=(str(body.base_build_id) if body.base_build_id else None):raise HTTPException(409,'构建版本已变化，请刷新')
    if body.message_id:
        message=db.scalar(select(Message).where(Message.id==str(body.message_id),Message.project_id==project.id,Message.role=='user'))
        if not message or message.content!=body.prompt:raise HTTPException(422,'消息与需求不匹配')
    else:
        message=Message(id=uid(),project_id=project.id,idempotency_key=str(body.idempotency_key),content=body.prompt);db.add(message);db.flush()
    run=enqueue(db,project,config,message,str(body.idempotency_key));db.commit();return run_view(run)

@router.get('/{project_id}/snapshot')
def snapshot(project_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=owned(db,project_id,user)
    run=db.scalar(select(GenerationRun).where(GenerationRun.project_id==project.id).order_by(GenerationRun.created_at.desc(),GenerationRun.id).limit(1))
    build=db.get(BuildArtifact,project.current_build_id) if project.current_build_id else None
    messages=db.scalars(select(Message).where(Message.project_id==project.id).order_by(Message.created_at,Message.id)).all()
    return {'run':run_view(run),'messages':[message_view(m) for m in messages], 'build':{'id':build.id,'number':build.number,'validation':build.validation,'mock':build.artifact.get('mock',False)} if build else None}

@router.post('/{project_id}/runs/{run_id}/stop')
def stop(project_id:UUID,run_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=owned(db,project_id,user)
    run=db.scalar(select(GenerationRun).where(GenerationRun.id==str(run_id),GenerationRun.project_id==project.id).with_for_update())
    if not run:raise HTTPException(404,'任务不可访问')
    if run.status in ACTIVE:
        run.status='cancelled' if run.status=='queued' else 'cancelling';add_event(run,run.status,'用户请求停止，保留旧构建');db.commit()
    return run_view(run)

@router.post('/{project_id}/runs/{run_id}/retry',status_code=202)
def retry(project_id:UUID,run_id:UUID,body:Retry,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=owned(db,project_id,user);advisory_lock(db,'model:'+user.id);advisory_lock(db,'generation:'+project.id)
    prior=db.scalar(select(GenerationRun).where(GenerationRun.id==str(run_id),GenerationRun.project_id==project.id))
    legacy=bool(prior and prior.status=='queued' and prior.provider!='mock' and prior.dispatch_version!=1)
    if not prior or (prior.status not in ('failed','cancelled','interrupted') and not legacy):raise HTTPException(409,'当前任务不允许模型重试')
    existing=db.scalar(select(GenerationRun).where(GenerationRun.project_id==project.id,GenerationRun.idempotency_key==str(body.idempotency_key)))
    if existing:return run_view(existing)
    config=enabled_config(db,user,body.config_id,body.config_version)
    require_worker(db,config.provider)
    if legacy:
        prior.status='cancelled';prior.finished_at=now();add_event(prior,'cancelled','用户手动重新提交，旧任务不执行');db.flush()
    run=enqueue(db,project,config,db.get(Message,prior.message_id),str(body.idempotency_key),prior.id);db.commit();return run_view(run)

@router.post('/{project_id}/runs/{run_id}/retry-save')
def retry_save(project_id:UUID,run_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=owned(db,project_id,user)
    run=db.scalar(select(GenerationRun).where(GenerationRun.id==str(run_id),GenerationRun.project_id==project.id))
    if not run or run.status!='save_failed':raise HTTPException(409,'无可重试保存候选')
    try:commit_candidate(run.id)
    except JobStopped:raise HTTPException(409,'任务或凭证已失效') from None
    return {'saved':True}

@router.post('/{project_id}/runs/{run_id}/revalidate')
def revalidate(project_id:UUID,run_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=owned(db,project_id,user);advisory_lock(db,'generation:'+project.id);advisory_lock(db,'model:'+user.id)
    run=db.scalar(select(GenerationRun).where(GenerationRun.id==str(run_id),GenerationRun.project_id==project.id).with_for_update())
    if run and run.status=='succeeded':return {'saved':True}
    if not run or run.status!='failed' or not (run.error or '').startswith(('应用缺少await atomsStorage','应用缺少异步atomsStorage')):
        raise HTTPException(409,'此失败结果不允许重新校验保存')
    config=enabled_config(db,user,run.config_id,run.config_version)
    if project.current_build_id!=run.base_build_id:raise HTTPException(409,'成功版本已变化，不能保存旧候选')
    if db.scalar(select(GenerationRun).where(GenerationRun.project_id==project.id,GenerationRun.status.in_(ACTIVE))):raise HTTPException(409,'已有活动任务')
    from app.services.artifacts import parse_output
    from app.api.application_sandbox import sandbox_validate
    from app.services.credentials import decrypt
    key=decrypt(config.ciphertext,config.owner_id,config.id,config.version)
    try:
        html=parse_output(run.stream_text);validation=sandbox_validate(html,key)
    finally:key=''
    run.candidate={'html':html,'validation':validation,'mock':False};run.status='validating';run.error=None
    add_event(run,'validating','用户重新校验已有完整产物，不调用模型');db.commit()
    try:commit_candidate(run.id)
    except JobStopped:raise HTTPException(409,'任务或凭证失效') from None
    return {'saved':True}

@router.get('/{project_id}/build')
def get_build(project_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=owned(db,project_id,user)
    build=db.get(BuildArtifact,project.current_build_id) if project.current_build_id else None
    if not build:raise HTTPException(404,'尚无成功构建')
    return {'id':build.id,'number':build.number,'html':build.artifact['html'],'validation':build.validation,'mock':build.artifact.get('mock',False)}
