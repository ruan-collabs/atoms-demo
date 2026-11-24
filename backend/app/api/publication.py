from uuid import UUID
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.auth import StrictInput
from app.api.projects import owned
from app.api.model_config import ACTIVE, enabled_config
from app.config import settings
from app.db import get_db, SessionLocal
from app.models import Publication, BuildArtifact, GenerationRun, User, now, uid
from app.security import current_user, advisory_lock
from app.application_server import preview_url

router=APIRouter(prefix='/projects',tags=['publication'])
class Publish(StrictInput):
    build_id: UUID
    idempotency_key: UUID


def publication_view(p,project):
    return {'status':p.status if p else 'unpublished','url':p.public_url if p else None,'published_build_id':p.published_build_id if p else None,'target_build_id':p.target_build_id if p else None,'error':p.error if p else None,'has_changes':bool(p and p.published_build_id and p.published_build_id!=project.current_build_id)}

@router.get('/{project_id}/preview-link')
def preview(project_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=owned(db,project_id,user)
    if not project.current_build_id:raise HTTPException(404,'暂无成功构建')
    build=db.get(BuildArtifact,project.current_build_id)
    if build and build.artifact.get('mock') and settings.dev_mock_sandbox and not settings.production:
        return {'url':settings.public_origin+'/mock-preview/'+project.id}
    from app.services.readiness import readiness
    if not readiness(db,'mock' if build and build.artifact.get('mock') else 'deepseek')['preview_ready']:
        raise HTTPException(503,'隔离预览服务未就绪，成功构建已保存')
    return {'url':preview_url(project.id,project.current_build_id)}

@router.get('/{project_id}/publication')
def get_publication(project_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=owned(db,project_id,user)
    publication=db.scalar(select(Publication).where(Publication.project_id==project.id))
    return publication_view(publication,project)

@router.post('/{project_id}/publish',status_code=202)
def publish(project_id:UUID,body:Publish,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=owned(db,project_id,user);advisory_lock(db,'generation:'+project.id);advisory_lock(db,'publication:'+project.id);enabled_config(db,user)
    p=db.scalar(select(Publication).where(Publication.project_id==project.id))
    if p and p.job_key==str(body.idempotency_key):return publication_view(p,project)
    if p and p.status in ('publishing','updating'):raise HTTPException(409,'发布任务正在进行')
    if db.scalar(select(GenerationRun).where(GenerationRun.project_id==project.id,GenerationRun.status.in_(ACTIVE))):raise HTTPException(409,'活动生成任务期间不能发布')
    if project.current_build_id!=str(body.build_id):raise HTTPException(409,'请发布当前成功构建')
    build=db.get(BuildArtifact,str(body.build_id))
    if not build or not build.validation.get('javascript_syntax'):raise HTTPException(409,'构建未通过校验')
    if build.artifact.get('mock') and settings.production:raise HTTPException(409,'生产禁止发布Mock产物')
    if build.artifact.get('mock') and settings.dev_mock_sandbox:
        from app.api.mock_sandbox import trusted_fixture
        trusted_fixture(build)
        if not p:p=Publication(id=uid(),project_id=project.id);db.add(p)
        p.published_build_id=str(body.build_id);p.target_build_id=str(body.build_id);p.job_key=str(body.idempotency_key)
        p.public_url=settings.public_origin+'/mock-apps/'+project.id
        p.status='published';p.error=None;p.updated_at=now();db.commit()
        return publication_view(p,project)
    from app.services.readiness import readiness
    state=readiness(db,'mock' if build.artifact.get('mock') else 'deepseek')
    if not state['preview_ready'] or not state['publication_ready'] or not state['worker_ready']:
        raise HTTPException(503,'发布服务未就绪，当前成功构建已保留')
    if not p:p=Publication(id=uid(),project_id=project.id);db.add(p)
    p.target_build_id=str(body.build_id);p.job_key=str(body.idempotency_key);p.status='updating' if p.published_build_id else 'publishing';p.error=None;p.updated_at=now();db.commit()
    return publication_view(p,project)

async def process_publication():
    with SessionLocal() as db:
        p=db.scalar(select(Publication).where(Publication.status.in_(('publishing','updating'))).order_by(Publication.updated_at).with_for_update(skip_locked=True).limit(1))
        if not p:return False
        pid,target,key=p.project_id,p.target_build_id,p.job_key
        build=db.get(BuildArtifact,target)
        # Verify saved artifact is reachable on isolated server before committing pointer.
        url=preview_url(pid,target)
        db.commit()
    from urllib.parse import urlsplit
    parts=urlsplit(url)
    try:
        connect_url=url if settings.production else 'http://127.0.0.1:'+str(parts.port or 8001)+'/'+('?' + parts.query)
        async with httpx.AsyncClient(timeout=10,trust_env=False,follow_redirects=False) as client:
            r=await client.get(connect_url,headers={'Host':parts.netloc})
        if settings.production and build.artifact.get('mock'):raise ValueError('Mock forbidden')
        expected=build.validation['sha256']
        if r.status_code!=200 or r.headers.get('X-Artifact-SHA256')!=expected:raise ValueError()
        app_url=settings.app_url(pid,True)
        public_parts=urlsplit(app_url)
        candidate_url=app_url+'?'+parts.query
        target_url=candidate_url if settings.production else f'http://127.0.0.1:{public_parts.port}/?'+parts.query
        async with httpx.AsyncClient(timeout=10,trust_env=False,follow_redirects=False) as client:
            public_response=await client.get(target_url,headers={'Host':public_parts.netloc})
        if public_response.status_code!=200 or public_response.headers.get('X-Artifact-SHA256')!=expected:raise ValueError()
        with SessionLocal() as db:
            p=db.scalar(select(Publication).where(Publication.project_id==pid).with_for_update())
            if p.job_key==key and p.target_build_id==target:
                p.published_build_id=target;p.public_url=settings.app_url(pid,True);p.status='published';p.error=None;p.updated_at=now();db.commit()
        return True
    except Exception:
        with SessionLocal() as db:
            p=db.scalar(select(Publication).where(Publication.project_id==pid).with_for_update())
            if p.job_key==key:
                p.status='failed';p.error='隔离应用资源可达校验失败，旧发布版本保留';db.commit()
        return True
