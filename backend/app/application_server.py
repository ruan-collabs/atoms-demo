"""Separate application origin service: no platform API or identity cookies."""
import hashlib
import hmac
import time
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from app.config import settings
from app.db import SessionLocal
from app.models import Project, BuildArtifact, Publication
from app.security import digest

app=FastAPI(docs_url=None,openapi_url=None,redoc_url=None)

def preview_signature(project_id,build_id,expires):
    return digest(f'preview:{project_id}:{build_id}:{expires}')

def preview_url(project_id,build_id):
    expires=int(time.time())+3600
    return settings.app_url(project_id)+f'?build={build_id}&expires={expires}&signature={preview_signature(project_id,build_id,expires)}'

def render_html(html):
    # Only runtime health information crosses origins; no access to platform credentials.
    bridge="""<script>(()=>{const send=(type)=>{try{parent.postMessage({type},'*')}catch{}};addEventListener('error',()=>send('atoms-preview-error'));addEventListener('unhandledrejection',()=>send('atoms-preview-error'));addEventListener('load',()=>send('atoms-preview-ready'));})();</script>"""
    source_html=html
    html=re.sub(r'</head\s*>',lambda m:bridge+m.group(0),html,count=1,flags=re.I)
    response=HTMLResponse(html)
    response.headers['Content-Security-Policy']="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; font-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; sandbox allow-scripts allow-same-origin allow-forms"
    response.headers['X-Artifact-SHA256']=hashlib.sha256(source_html.encode()).hexdigest()
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    return response

@app.get('/health')
def health():return {'status':'ok','service':'isolated-application'}

@app.get('/')
def application(request:Request):
    host=request.headers.get('host','').split(':')[0]
    match=re.fullmatch(r'([pa])-([0-9a-f-]{36})\.(.+)',host)
    if not match:return JSONResponse(status_code=404,content={'detail':'应用不可访问'})
    kind,project_id,suffix=match.groups()
    from urllib.parse import urlsplit
    expected=urlsplit(settings.preview_origin if kind=='p' else settings.app_origin).hostname
    if suffix!=expected:return JSONResponse(status_code=404,content={'detail':'应用不可访问'})
    with SessionLocal() as db:
        if kind=='p' or request.query_params.get('build'):
            build_id=request.query_params.get('build','');expires=request.query_params.get('expires','');signature=request.query_params.get('signature','')
            try:
                if int(expires)<time.time() or not hmac.compare_digest(signature,preview_signature(project_id,build_id,expires)):raise ValueError()
            except ValueError:return JSONResponse(status_code=404,content={'detail':'预览链接已失效'})
            build=db.scalar(select(BuildArtifact).where(BuildArtifact.id==build_id,BuildArtifact.project_id==project_id))
        else:
            publication=db.scalar(select(Publication).where(Publication.project_id==project_id))
            build=db.get(BuildArtifact,publication.published_build_id) if publication and publication.published_build_id else None
        if not build or (settings.production and build.artifact.get('mock')):return JSONResponse(status_code=404,content={'detail':'应用尚未发布或不可访问'})
        return render_html(build.artifact['html'])
