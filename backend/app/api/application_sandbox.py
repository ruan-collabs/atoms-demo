"""Real generated artifacts: opaque sandbox + narrow async storage contract.

This is not the Mock fixture exception. No same-origin permission, platform APIs,
credentials, arbitrary files, network or arbitrary storage keys are delegated.
"""
import hashlib
import re
import secrets
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import settings
from app.db import get_db
from app.models import BuildArtifact, Publication
from app.security import current_user
from app.api.projects import owned
from app.services.artifacts import validate_html
from app.services.provider import ProviderError

router=APIRouter(prefix='/application-sandbox',tags=['application sandbox'])


def sandbox_validate(html,key=''):
    result=validate_html(html,key)
    if re.search(r'\b(?:localStorage|sessionStorage|indexedDB)\b|document\s*\.\s*cookie',html):
        raise ProviderError('沙箱应用必须使用异步atomsStorage，不允许浏览器原生存储','artifact')
    if 'atomsStorage' not in html or not re.search(r'(?:window\.)?atomsStorage\.setItem\s*\(',html) or not ('await ' in html or '.then(' in html):
        raise ProviderError('应用缺少异步atomsStorage.setItem持久化契约','artifact')
    class Contract(HTMLParser):
        def handle_starttag(self,tag,attrs):
            if tag=='script' and dict(attrs).get('type','') not in ('','text/javascript','application/javascript'):
                raise ProviderError('沙箱仅支持内联经典脚本','artifact')
            if any(k.startswith('on') or k in ('srcdoc','nonce','formaction','data-atoms-script') for k,v in attrs):
                raise ProviderError('沙箱应用需使用addEventListener，不允许内联事件或嵌套执行内容','artifact')
    Contract().feed(html)
    result['sandbox_contract']='atoms-storage-v1'
    return result


class Renderer(HTMLParser):
    """Parse serialized HTML; scripts execute only after storage initialization.

    Escape program text inside inert HTML blocks to prevent </script> surprises.
    Generated code is never evaluated by Python or the parent page.
    """
    def __init__(self,bootstrap):
        super().__init__(convert_charrefs=False);self.parts=[];self.in_script=False;self.script='';self.injected=False;self.bootstrap=bootstrap;self.scripts=[]
    def handle_starttag(self,tag,attrs):
        if tag=='script':self.in_script=True;self.script='';return
        self.parts.append(self.get_starttag_text())
        if tag=='head' and not self.injected:self.parts.append(self.bootstrap);self.injected=True
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs)
    def handle_endtag(self,tag):
        if tag=='script' and self.in_script:
            self.scripts.append('<template data-atoms-script>'+escape(self.script)+'</template>');self.in_script=False;return
        if tag=='body':self.parts.extend(self.scripts);self.scripts=[]
        self.parts.append('</'+tag+'>')
    def handle_data(self,data):
        if self.in_script:self.script+=data
        else:self.parts.append(data)
    def handle_entityref(self,name):self.handle_data('&'+name+';')
    def handle_charref(self,name):self.handle_data('&#'+name+';')
    def handle_comment(self,data):
        if self.in_script:self.script+='<!--'+data+'-->'
        else:self.parts.append('<!--'+data+'-->')
    def handle_decl(self,decl):self.parts.append('<!'+decl+'>')


def render_frame(build,channel):
    html=build.artifact.get('html','')
    if build.artifact.get('mock') or build.validation.get('sandbox_contract')!='atoms-storage-v1':
        raise HTTPException(409,'此构建未采用真实应用沙箱契约，请重新生成')
    if hashlib.sha256(html.encode()).hexdigest()!=build.validation.get('sha256'):
        raise HTTPException(409,'构建完整性校验失败')
    runtime=Path(settings.frontend_dist)/'application-sandbox-child.js'
    if not runtime.is_file():raise HTTPException(503,'沙箱运行资源未构建')
    nonce=secrets.token_urlsafe(24)
    bootstrap=f'<script nonce="{nonce}" data-channel="{channel}" data-build="{build.id}">'+runtime.read_text(encoding='utf-8')+'</script>'
    parser=Renderer(bootstrap);parser.feed(html)
    if not parser.injected:raise HTTPException(409,'应用缺少head入口')
    response=HTMLResponse(''.join(parser.parts))
    response.headers['Content-Security-Policy']=f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; font-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'; sandbox allow-scripts allow-forms"
    response.headers['X-Frame-Options']='SAMEORIGIN'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    response.headers['Cache-Control']='no-store'
    response.headers['X-Artifact-SHA256']=build.validation['sha256']
    return response


def public_build(db,pid):
    publication=db.scalar(select(Publication).where(Publication.project_id==str(pid),Publication.published_build_id.is_not(None)))
    build=db.get(BuildArtifact,publication.published_build_id) if publication else None
    if not build or build.artifact.get('mock') or build.validation.get('sandbox_contract')!='atoms-storage-v1':
        raise HTTPException(404,'应用尚未发布')
    return build


def available():
    if not settings.application_sandbox:raise HTTPException(404,'应用沙箱未启用')


@router.get('/{project_id}/public')
def public_snapshot(project_id:UUID,db:Session=Depends(get_db)):
    available();build=public_build(db,project_id)
    return {'id':build.id,'number':build.number,'mock':False,'sandbox':True}


@router.get('/{project_id}/frame')
def frame(project_id:UUID,request:Request,channel:UUID,build_id:UUID,public_view:bool=False,db:Session=Depends(get_db)):
    available()
    if public_view:
        build=public_build(db,project_id)
        if build.id!=str(build_id):raise HTTPException(409,'公开版本已更新，请刷新')
    else:
        user=current_user(request,db);owned(db,project_id,user)
        build=db.scalar(select(BuildArtifact).where(BuildArtifact.project_id==str(project_id),BuildArtifact.id==str(build_id)))
        if not build:raise HTTPException(404,'构建不可访问')
    return render_frame(build,str(channel))
