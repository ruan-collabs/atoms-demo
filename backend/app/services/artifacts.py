import hashlib
import json
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from app.services.provider import ProviderError

class ArtifactParser(HTMLParser):
    def __init__(self):super().__init__();self.scripts=[];self.inscript=False;self.script='';self.has_body=False;self.has_html=False
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if tag=='html':self.has_html=True
        if tag=='body':self.has_body=True
        if tag in ('iframe','object','embed','base','meta') and (tag!='meta' or 'http-equiv' in values):
            raise ProviderError('产物包含不允许的嵌入或重定向','artifact')
        for key,value in attrs:
            if key in ('src','href','action') and value and not value.startswith(('#','data:image/')):
                raise ProviderError('P0仅支持内联代码与图片，不允许外部资源或网络跳转','artifact')
        if tag=='script':self.inscript=True;self.script=''
    def handle_endtag(self,tag):
        if tag=='script':self.inscript=False;self.scripts.append(self.script)
    def handle_data(self,data):
        if self.inscript:self.script+=data

def parse_output(text):
    value=text.strip()
    if value.startswith('```'):
        value=re.sub(r'^```(?:html|json)?\s*','',value);value=re.sub(r'\s*```$','',value)
    if value.startswith('{'):
        try:value=json.loads(value)['html']
        except (ValueError,KeyError,TypeError):raise ProviderError('模型产物结构无效','artifact') from None
    return value

def validate_html(html,key=''):
    if not isinstance(html,str) or len(html.encode())>500_000 or '<!doctype html' not in html.lower() or '</html>' not in html.lower():
        raise ProviderError('缺少完整HTML入口或超出500KB限制','artifact')
    if key and key in html:raise ProviderError('候选命中凭证，拒绝保存','leak')
    parser=ArtifactParser()
    try:parser.feed(html)
    except ProviderError:raise
    except Exception:raise ProviderError('HTML结构校验失败','artifact') from None
    if not parser.has_html or not parser.has_body:raise ProviderError('HTML缺少body','artifact')
    for script in parser.scripts:
        # Only parse JavaScript. Never execute generated code on the server.
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'candidate.js';path.write_text(script,encoding='utf-8')
            try:result=subprocess.run(['node','--check',str(path)],capture_output=True,timeout=5)
            except (OSError,subprocess.TimeoutExpired):raise ProviderError('脚本语法校验器不可用','artifact') from None
            if result.returncode:raise ProviderError('JavaScript语法校验失败','artifact')
    return {'html':True,'javascript_syntax':True,'external_resources':False,'sha256':hashlib.sha256(html.encode()).hexdigest(),'scope':'结构与语法校验，不等于全部功能验收'}
