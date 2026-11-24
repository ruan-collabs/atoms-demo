"""Durable Postgres jobs; run as a separate process, never attached to browser lifetime."""
import asyncio
import json
import time
from datetime import timedelta
from sqlalchemy import select
from app.config import settings
from app.db import SessionLocal
from app.models import GenerationRun, ModelConfiguration, ModelDraft, Project, Message, BuildArtifact, now, uid
from app.services.credentials import decrypt, CredentialError
from app.services.provider import completion, stream_completion, ProviderError
from app.services.readiness import heartbeat
from app.services.mock_model import mock_completion
from app.services.artifacts import parse_output, validate_html
from app.security import advisory_lock

ACTIVE=('planning','generating','validating','cancelling')
TERMINAL=('succeeded','failed','interrupted','cancelled','save_failed')

def add_event(run,stage,detail):
    events=list(run.events or []);events.append({'seq':len(events)+1,'stage':stage,'detail':detail,'time':now().isoformat()});run.events=events

class JobStopped(Exception):pass

def valid_job(db,run_id,worker_token):
    run=db.scalar(select(GenerationRun).where(GenerationRun.id==run_id).with_for_update())
    if not run or run.status in TERMINAL or run.worker_token!=worker_token:raise JobStopped()
    if run.status=='cancelling':
        run.status='cancelled';run.finished_at=now();add_event(run,'cancelled','用户停止，旧构建保留');db.commit();raise JobStopped()
    config=db.get(ModelConfiguration,run.config_id)
    if not config or config.owner_id!=db.get(Project,run.project_id).owner_id or not config.enabled or config.deleted_at or config.version!=run.config_version or not config.ciphertext:
        run.status='cancelled';run.error='凭证已失效或删除';run.finished_at=now();db.commit();raise JobStopped()
    if run.lease_expires_at and run.lease_expires_at<now():raise JobStopped()
    return run,config

def transition(run_id,token,stage,detail):
    with SessionLocal() as db:
        run,_=valid_job(db,run_id,token);run.status=stage;run.lease_expires_at=now()+timedelta(seconds=settings.lease_seconds);add_event(run,stage,detail);db.commit()

async def guarded_call(run_id,token,call):
    task=asyncio.create_task(call)
    try:
        while not task.done():
            await asyncio.sleep(0.3)
            with SessionLocal() as db:
                run,_=valid_job(db,run_id,token);run.lease_expires_at=now()+timedelta(seconds=settings.lease_seconds);db.commit()
        return await task
    except BaseException:
        task.cancel()
        await asyncio.gather(task,return_exceptions=True)
        raise

async def execute(run_id,token):
    key=''
    try:
        with SessionLocal() as db:
            run,config=valid_job(db,run_id,token)
            message=db.get(Message,run.message_id);project=db.get(Project,run.project_id)
            base=db.get(BuildArtifact,run.base_build_id) if run.base_build_id else None
            base_html=base.artifact['html'] if base else None
            if config.provider=='mock':
                if settings.production or not settings.dev_mock_model:raise ProviderError('Mock模型已禁用','scope')
                key='MOCK-NON-SECRET'
            else:
                key=decrypt(config.ciphertext,config.owner_id,config.id,config.version)
            prompt=message.content
            provider=config.provider
            # Detached config snapshot, never store plaintext on a queue/run.
            config_snapshot=config
        candidate_for_repair=None
        plan=''
        pending=''
        last_flush=0.0
        async def on_delta(delta, force=False):
            nonlocal pending, last_flush
            pending += delta
            if not force and len(pending) < 4096 and time.monotonic() - last_flush < 0.4:
                return
            if not pending: return
            with SessionLocal() as db:
                run,_=valid_job(db,run_id,token)
                run.stream_text += pending
                run.stream_bytes = len(run.stream_text.encode())
                if run.stream_bytes > 1_000_000: raise ProviderError('产物超过大小限制','artifact')
                db.commit()
            pending='';last_flush=time.monotonic()
        async def call(stage,repair=None):
            nonlocal pending
            if stage != 'planning':
                pending=''
                with SessionLocal() as db:
                    r,_=valid_job(db,run_id,token);r.stream_text='';r.stream_bytes=0;r.stream_revision+=1;db.commit()
            if provider=='mock':
                value=await guarded_call(run_id,token,mock_completion(prompt,base_html,planning=stage=='planning'))
                if stage != 'planning':
                    # A completed fixture is not disguised as token streaming.
                    await on_delta(value,force=True)
                return value
            system='You build self-contained single-page HTML/CSS/JS applications. No external resources, no remote fetch, no server code, payments or sensitive services. Use inline CSS/JS. Never include credentials. Use persistent JSON application data and show failures. Preserve existing storage schema on style iterations. Output complete <!doctype html> document, not Markdown.'
            if settings.application_sandbox:
                system += ' Use window.atomsStorage only (provided by the sandbox): getItem("atoms-app:data:v1") returns JSON string or null; await atomsStorage.setItem("atoms-app:data:v1", JSON.stringify(objectOrArray)) resolves only after durable browser save. Initialize from getItem, validate JSON. Every mutation must await setItem before updating UI. No localStorage/sessionStorage/indexedDB/cookies. Use addEventListener; no inline onclick or other event attributes. Include head and classic inline scripts. Data must be JSON object or array under 200KB. Do not define atomsStorage yourself.'
            if stage=='planning':
                if any(term in prompt for term in ('真实支付','真实医疗','多人共享数据库','真实银行')):raise ProviderError('P0仅支持本地单页应用，不支持此真实敏感服务需求','scope')
                msgs=[{'role':'system','content':'Return concise JSON with scope, components, interactions, storage and acceptance. Only support local single-page apps. Do not expose hidden reasoning.'},{'role':'user','content':prompt}]
            else:
                msgs=[{'role':'system','content':system}]
                if base_html:msgs.append({'role':'user','content':'Existing application (preserve behavior and storage):\n'+base_html})
                if plan:msgs.append({'role':'user','content':'Scope plan (not user approval):\n'+plan})
                if repair and candidate_for_repair:msgs.append({'role':'user','content':'Candidate to repair:\n'+candidate_for_repair})
                msgs.append({'role':'user','content':prompt+(('\nFix validation issue: '+repair) if repair else '')})
            if stage == 'planning':
                return await guarded_call(run_id,token,completion(config_snapshot,key,msgs,max_tokens=1024))
            value=await guarded_call(run_id,token,stream_completion(config_snapshot,key,msgs,on_delta))
            await on_delta('',force=True)
            return value
        async with asyncio.timeout(settings.run_budget_seconds):
            transition(run_id,token,'planning','开始范围与交互规划'+('（开发Mock）' if provider=='mock' else ''))
            plan=await call('planning')
            with SessionLocal() as db:
                run,_=valid_job(db,run_id,token)
                db.add(Message(project_id=run.project_id,idempotency_key=__import__('hashlib').sha256((run.id+':plan').encode()).hexdigest()[:36],role='assistant',content='规划助手'+(' [Mock]' if provider=='mock' else '')+'\n'+plan));db.commit()
            transition(run_id,token,'generating','在当前成功构建基础上生成' if base_html else '生成完整应用代码')
            candidate=parse_output(await call('generating'))
            transition(run_id,token,'validating','检查HTML入口、脚本语法、外部资源与凭证泄漏')
            validate=validate_html
            if settings.application_sandbox and provider!='mock':
                from app.api.application_sandbox import sandbox_validate
                validate=sandbox_validate
            try:validation=await asyncio.to_thread(validate,candidate,key)
            except ProviderError as exc:
                if exc.category=='leak':raise
                candidate_for_repair=candidate
                transition(run_id,token,'generating','一次修复尝试（可能再次计费，不无限重试）')
                candidate=parse_output(await call('generating',repair=str(exc)))
                transition(run_id,token,'validating','修复后重新校验')
                validation=await asyncio.to_thread(validate,candidate,key)
            with SessionLocal() as db:
                run,_=valid_job(db,run_id,token)
                run.candidate={'html':candidate,'validation':validation,'mock':provider=='mock'}
                db.commit()
            commit_candidate(run_id,token)
    except JobStopped:pass
    except (ProviderError,CredentialError,TimeoutError) as exc:
        with SessionLocal() as db:
            run=db.scalar(select(GenerationRun).where(GenerationRun.id==run_id).with_for_update())
            if run and run.status not in TERMINAL:
                run.status='failed';run.error='任务超过执行预算' if isinstance(exc,TimeoutError) else str(exc);run.finished_at=now();add_event(run,'failed',run.error)
                if isinstance(exc,ProviderError) and exc.category=='auth':
                    config=db.get(ModelConfiguration,run.config_id)
                    if config:config.enabled=False
                db.commit()
    except Exception as exc:
        print('Worker failed (type only, no payload): '+type(exc).__name__,flush=True)
        # Unknown upstream result: do not replay a possibly charged request.
        try:
            with SessionLocal() as db:
                run=db.get(GenerationRun,run_id)
                if run and run.status not in TERMINAL:
                    run.status='save_failed' if run.candidate else 'interrupted';run.error='执行或保存异常；不自动重发模型请求';run.finished_at=now();db.commit()
        except Exception:pass
    finally:key=''

def commit_candidate(run_id,token=None):
    with SessionLocal() as db:
        run=db.scalar(select(GenerationRun).where(GenerationRun.id==run_id).with_for_update())
        if not run or not run.candidate or run.status not in ('validating','save_failed'):raise JobStopped()
        if token and run.worker_token!=token:raise JobStopped()
        config=db.get(ModelConfiguration,run.config_id)
        if not config or not config.enabled or config.deleted_at or config.version!=run.config_version:raise JobStopped()
        project=db.scalar(select(Project).where(Project.id==run.project_id).with_for_update())
        if project.current_build_id!=run.base_build_id:raise ProviderError('成功构建已变化，请刷新后重试','conflict')
        builds=db.scalars(select(BuildArtifact).where(BuildArtifact.project_id==project.id)).all()
        artifact=BuildArtifact(id=uid(),project_id=project.id,run_id=run.id,number=max([x.number for x in builds],default=0)+1,artifact={'html':run.candidate['html'],'mock':run.candidate['mock']},validation=run.candidate['validation'])
        db.add(artifact);db.flush();project.current_build_id=artifact.id;project.updated_at=now()
        run.status='succeeded';run.finished_at=now();run.candidate=None;add_event(run,'succeeded',f'构建{artifact.number}已校验保存')
        db.add(Message(project_id=project.id,idempotency_key=__import__('hashlib').sha256((run.id+':result').encode()).hexdigest()[:36],role='assistant',content=f"构建助手{' [Mock]' if artifact.artifact['mock'] else ''}\n构建 {artifact.number} 已保存。验证范围：HTML结构、JS语法、外部资源限制；功能行为请在预览中验证。本浏览器应用数据不承诺云同步。"))
        db.commit()

def maintenance_and_claim(mock_only=False):
    with SessionLocal() as db:
        for draft in db.scalars(select(ModelDraft).where(ModelDraft.expires_at<now(),ModelDraft.ciphertext.is_not(None))):
            draft.ciphertext=None;draft.status='expired'
        for stale in db.scalars(select(GenerationRun).where(GenerationRun.status.in_(ACTIVE),GenerationRun.lease_expires_at<now()).with_for_update(skip_locked=True)):
            stale.status='interrupted';stale.error='Worker租约过期，未知上游结果不会自动重放';stale.finished_at=now();add_event(stale,'interrupted',stale.error)
        for waiting in db.scalars(select(GenerationRun).where(GenerationRun.status=='queued',GenerationRun.provider!='mock',GenerationRun.dispatch_version==1,GenerationRun.created_at<now()-timedelta(seconds=60)).with_for_update(skip_locked=True)):
            waiting.status='interrupted';waiting.finished_at=now();waiting.error='任务未被及时认领，请手动重新提交；未自动调用模型';add_event(waiting,'interrupted',waiting.error)
        query=select(GenerationRun).where(GenerationRun.status=='queued')
        # Version-zero real jobs predate readiness gates. Never consume old backlog implicitly.
        from sqlalchemy import or_
        query=query.where(or_(GenerationRun.provider=='mock',GenerationRun.dispatch_version==1))
        if mock_only:query=query.where(GenerationRun.provider=='mock')
        elif not settings.dev_mock_model:query=query.where(GenerationRun.provider!='mock')
        run=db.scalar(query.order_by(GenerationRun.created_at).with_for_update(skip_locked=True).limit(1))
        if not run:db.commit();return None
        run.worker_token=uid();run.status='planning';run.lease_expires_at=now()+timedelta(seconds=settings.lease_seconds);db.commit();return run.id,run.worker_token

async def main(mock_only=False):
    print('Atoms Worker ready; durable Postgres queue; no request/key logging',flush=True)
    service_id=uid()
    async def pulse():
        while True:
            try: await asyncio.to_thread(heartbeat,service_id,'worker',mock_only)
            except Exception: pass
            await asyncio.sleep(5)
    pulse_task=asyncio.create_task(pulse())
    try:
        while True:
            try:
                from app.api.publication import process_publication
                if not mock_only:await process_publication()
                job=maintenance_and_claim(mock_only=mock_only)
                if job:await execute(*job)
                else:await asyncio.sleep(settings.worker_poll_seconds)
            except asyncio.CancelledError:raise
            except Exception:await asyncio.sleep(2)
    finally:
        pulse_task.cancel();await asyncio.gather(pulse_task,return_exceptions=True)

if __name__=='__main__':asyncio.run(main())
