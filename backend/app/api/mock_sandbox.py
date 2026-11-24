"""Mock-only opaque-origin sandbox, never an execution route for real model artifacts."""
import re
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter,Depends,HTTPException,Query,Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.config import settings
from app.db import get_db
from app.security import current_user
from app.models import User,Project,BuildArtifact,Publication
from app.api.projects import owned

router=APIRouter(prefix='/mock-sandbox',tags=['mock sandbox'])

def available():
    if settings.production or not settings.dev_mock_sandbox or not settings.dev_mock_model:
        raise HTTPException(404,'Mock沙箱不可用')

def public_build(db,pid):
    available()
    publication=db.scalar(select(Publication).where(Publication.project_id==str(pid),Publication.status=='published'))
    build=db.get(BuildArtifact,publication.published_build_id) if publication else None
    if not build or not build.artifact.get('mock'):raise HTTPException(404,'Mock应用尚未发布')
    return build

def trusted_fixture(build):
    # Only exact project-owned trusted fixtures (with supported accent changes) can
    # acquire the limited storage bridge. A mock flag alone is insufficient.
    html=build.artifact.get('html','')
    normalized=re.sub(r'--accent:#[0-9a-fA-F]{6}','--accent:#4f74ed',html)
    fixtures=Path(__file__).resolve().parents[1]/'fixtures'
    if normalized.strip() not in [(fixtures/name).read_text().strip() for name in ('tasks.html','portfolio.html')]:
        raise HTTPException(409,'旧Mock构建不支持沙箱，请重新生成此演示项目')
    return html

@router.get('/{project_id}/public')
def public_snapshot(project_id:UUID,db:Session=Depends(get_db)):
    build=public_build(db,project_id)
    return {'id':build.id,'number':build.number,'html':trusted_fixture(build),'mock':True}

@router.get('/{project_id}/frame')
def frame(project_id:UUID,request:Request,channel:UUID,public_view:bool=False,db:Session=Depends(get_db)):
    available()
    if public_view:build=public_build(db,project_id)
    else:
        user=current_user(request,db)
        project=owned(db,project_id,user)
        build=db.get(BuildArtifact,project.current_build_id) if project.current_build_id else None
        if not build or not build.artifact.get('mock'):raise HTTPException(404,'没有Mock构建')
    html=trusted_fixture(build)
    html=re.sub(r'<script\b[^>]*>([\s\S]*?)</script\s*>',lambda m:'<script type="application/x-atoms-mock">'+m.group(1)+'</script>',html,flags=re.I)
    bridge=f'<script src="/mock-sandbox-child.js" data-channel="{channel}"></script>'
    html=re.sub(r'<head\b[^>]*>',lambda m:m.group(0)+bridge,html,count=1,flags=re.I)
    response=HTMLResponse(html)
    response.headers['Content-Security-Policy']="default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'; sandbox allow-scripts allow-forms"
    response.headers['X-Frame-Options']='SAMEORIGIN'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    response.headers['Cache-Control']='no-store'
    return response
