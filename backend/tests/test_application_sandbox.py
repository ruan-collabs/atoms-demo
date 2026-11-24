"""Opaque real-artifact contract tests. No live model calls."""
import uuid
from pathlib import Path
import pytest
from sqlalchemy import select
from app.config import settings
from app.db import SessionLocal
from app.models import BuildArtifact
from app.api.application_sandbox import sandbox_validate,render_frame
from app.services.provider import ProviderError
from test_generation import create,finish,snapshot

HTML='''<!doctype html><html><head><title>notes</title></head><body><input id="entry"><button id="save">save</button><p id="result"></p><script>
const data=JSON.parse(atomsStorage.getItem('atoms-app:data:v1')||'[]');
document.querySelector('#result').textContent=data.join(',');
document.querySelector('#save').addEventListener('click',async()=>{const next=[...data,document.querySelector('#entry').value];await atomsStorage.setItem('atoms-app:data:v1',JSON.stringify(next));data.splice(0,data.length,...next);document.querySelector('#result').textContent=data.join(',');});
</script></body></html>'''

@pytest.fixture
def sandbox(monkeypatch):
 monkeypatch.setattr(settings,'application_sandbox',True)
 monkeypatch.setattr(settings,'frontend_dist',str(Path(__file__).resolve().parents[2]/'frontend/public'))


def real_build(client):
 pid=create(client);finish()
 with SessionLocal() as db:
  b=db.scalar(select(BuildArtifact).where(BuildArtifact.project_id==pid));b.artifact={'html':HTML,'mock':False};b.validation=sandbox_validate(HTML);db.commit();bid=b.id
 return pid,bid


def test_real_frame_csp_no_same_origin_and_no_auth_leaks(client,login,sandbox):
 login(client);pid,bid=real_build(client)
 response=client.get(f'/api/application-sandbox/{pid}/frame?build_id={bid}&channel={uuid.uuid4()}')
 assert response.status_code==200,response.text
 csp=response.headers['content-security-policy'];assert 'allow-same-origin' not in csp and "connect-src 'none'" in csp and "script-src 'nonce-" in csp
 assert 'data-atoms-script' in response.text and '&#x27;' in response.text
 assert 'csrf_token' not in response.text and 'ciphertext' not in response.text
 login(client,'bob@example.com')
 assert client.get(f'/api/application-sandbox/{pid}/frame?build_id={bid}&channel={uuid.uuid4()}').status_code==404


def test_only_published_artifact_public_and_private_requires_auth(client,login,sandbox):
 login(client);pid,bid=real_build(client)
 assert client.get(f'/api/application-sandbox/{pid}/public').status_code==404
 r=client.post(f'/api/projects/{pid}/publish',json={'build_id':bid,'idempotency_key':str(uuid.uuid4())})
 assert r.status_code==202 and r.json()['url'].endswith('/apps/'+pid)
 client.post('/api/auth/logout')
 assert client.get(f'/api/application-sandbox/{pid}/public').json()['id']==bid
 assert client.get(f'/api/application-sandbox/{pid}/frame?build_id={bid}&public_view=true&channel={uuid.uuid4()}').status_code==200
 assert client.get(f'/api/application-sandbox/{pid}/frame?build_id={bid}&channel={uuid.uuid4()}').status_code==401


@pytest.mark.parametrize('bad',[HTML.replace('atomsStorage','localStorage'),HTML.replace('await atomsStorage','atomsStorage'),HTML.replace('<button id="save">','<button onclick="alert(1)" id="save">'),HTML.replace('<script>','<script type="module">')])
def test_storage_and_execution_contract_fail_closed(bad):
 with pytest.raises(ProviderError):sandbox_validate(bad)


def test_promise_contract_and_revalidate_without_model(client,login,sandbox):
 from app.models import GenerationRun,ModelConfiguration
 from app.services.credentials import encrypt
 login(client);pid=create(client)
 html=HTML.replace('await atomsStorage.setItem(\'atoms-app:data:v1\',JSON.stringify(next));','return atomsStorage.setItem(\'atoms-app:data:v1\',JSON.stringify(next)).then(()=>{').replace("data.join(',');});\n</script>","data.join(',');});});\n</script>")
 assert sandbox_validate(html)['sandbox_contract']=='atoms-storage-v1'
 with SessionLocal() as db:
  run=db.scalar(select(GenerationRun).where(GenerationRun.project_id==pid));run.provider='deepseek';run.status='failed';run.error='应用缺少await atomsStorage.setItem持久化契约';run.stream_text=html
  config=db.get(ModelConfiguration,run.config_id);config.provider='deepseek';config.ciphertext=encrypt('fixture-only-key',config.owner_id,config.id,config.version);db.commit();rid=run.id
 assert client.post(f'/api/projects/{pid}/runs/{rid}/revalidate').status_code==200
 assert snapshot(client,pid)['run']['status']=='succeeded'


def test_mock_cannot_use_real_sandbox_and_integrity_check(client,login,sandbox):
 login(client);pid=create(client);finish();bid=snapshot(client,pid)['build']['id']
 assert client.get(f'/api/application-sandbox/{pid}/frame?build_id={bid}&channel={uuid.uuid4()}').status_code==409
