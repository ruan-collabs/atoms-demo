import asyncio
import base64
import uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
import pytest
from sqlalchemy import select,func
from app.config import Settings,settings
from app.db import SessionLocal
from app.models import ModelConfiguration,ModelDraft,GenerationRun,Project,BuildArtifact,Publication,Message,now
from app.services.credentials import encrypt,decrypt,CredentialError
from app.services.provider import resolve_target,ProviderError
from app.services.artifacts import validate_html
from app.worker import maintenance_and_claim,execute
from app.application_server import app as isolated,preview_url
from fastapi.testclient import TestClient


def configuration(client):return client.get('/api/model-config').json()['config']
def create(client,prompt='创建任务管理应用'):
    r=client.post('/api/projects',json={'prompt':prompt,'idempotency_key':str(uuid.uuid4())});assert r.status_code==201,r.text;return r.json()['id']
def finish():
    job=maintenance_and_claim();assert job;asyncio.run(execute(*job))
def snapshot(client,pid):return client.get(f'/api/projects/{pid}/snapshot').json()
def generate(client,pid,prompt,key=None):
    config=configuration(client);snap=snapshot(client,pid)
    return client.post(f'/api/projects/{pid}/generate',json={'prompt':prompt,'idempotency_key':key or str(uuid.uuid4()),'config_id':config['id'],'config_version':config['version'],'base_build_id':snap['build']['id'] if snap['build'] else None})

@pytest.fixture(autouse=True)
def fast_mock(monkeypatch):monkeypatch.setattr(settings,'mock_delay_seconds',0.01)

def test_mock_disabled_endpoint(client,monkeypatch):
    monkeypatch.setattr(settings,'dev_mock_auth',False)
    assert client.post('/api/dev/mock-login',json={'account':'alice'}).status_code==404

def test_hard_gate_without_config(client,mailbox):
    challenge=client.post('/api/auth/email/code',json={'email':'gate@example.com','terms_accepted':True}).json()['challenge_id']
    r=client.post('/api/auth/email/verify',json={'challenge_id':challenge,'code':mailbox[-1][1]});client.headers['X-CSRF-Token']=r.json()['csrf_token']
    assert client.post('/api/projects',json={'prompt':'test','idempotency_key':str(uuid.uuid4())}).status_code==428
    with SessionLocal() as db:assert db.scalar(select(func.count()).select_from(Project))==0

def test_aes_authenticated_binding_and_random_nonce():
    a=encrypt('fixture-secret','owner','cfg',1);b=encrypt('fixture-secret','owner','cfg',1)
    assert a!=b and 'fixture-secret' not in a
    assert decrypt(a,'owner','cfg',1)=='fixture-secret'
    for owner,version in [('another',1),('owner',2)]:
        with pytest.raises(CredentialError):decrypt(a,owner,'cfg',version)
    with pytest.raises(CredentialError):decrypt(a[:-8]+'00000000','owner','cfg',1)

def test_encrypted_database_and_no_key_api(client,login):
    login(client)
    result=client.get('/api/model-config');assert 'MOCK-NON-SECRET' not in result.text and 'ciphertext' not in result.text
    with SessionLocal() as db:
        c=db.scalar(select(ModelConfiguration));assert c.ciphertext and 'MOCK-NON-SECRET' not in c.ciphertext
        assert decrypt(c.ciphertext,c.owner_id,c.id,c.version)=='MOCK-NON-SECRET'
        assert db.scalar(select(ModelDraft)).ciphertext is None

def test_expired_or_foreign_draft_cannot_save(client,login):
    login(client);r=client.post('/api/model-config/test',json={'provider':'mock','api_key':'','base_url':'mock://local','model':'fixture','idempotency_key':str(uuid.uuid4()),'consent':True})
    did=r.json()['draft_id']
    with SessionLocal() as db:db.get(ModelDraft,did).expires_at=now()-timedelta(seconds=1);db.commit()
    assert client.post('/api/model-config/save',json={'draft_id':did,'consent':True}).status_code==409

def test_worker_real_persistence_different_fixtures(client,login):
    login(client);a=create(client);finish();b=create(client,'个人作品集');finish()
    first=client.get(f'/api/projects/{a}/build').json();second=client.get(f'/api/projects/{b}/build').json()
    assert first['mock'] and second['mock'];assert first['html']!=second['html'];assert '任务标题' in first['html'];assert '精选作品' in second['html']
    assert snapshot(client,a)['run']['status']=='succeeded'
    with SessionLocal() as db:assert db.scalar(select(func.count()).select_from(BuildArtifact))==2

def test_iteration_preserves_data_key_and_public_pointer(client,login):
    login(client);pid=create(client);finish();old=client.get(f'/api/projects/{pid}/build').json()
    with SessionLocal() as db:db.add(Publication(project_id=pid,published_build_id=old['id'],status='published'));db.commit()
    assert generate(client,pid,'主色改成紫色').status_code==202;finish();new=client.get(f'/api/projects/{pid}/build').json()
    assert new['number']==2 and '--accent:#8b5cf6' in new['html'] and "atoms-app:tasks:v1" in new['html']
    assert client.get(f'/api/projects/{pid}/publication').json()['published_build_id']==old['id']

def test_failure_does_not_overwrite_build(client,login):
    login(client);pid=create(client);finish();old=snapshot(client,pid)['build']['id']
    assert generate(client,pid,'[mock:fail]').status_code==202;finish()
    assert snapshot(client,pid)['run']['status']=='failed';assert snapshot(client,pid)['build']['id']==old

def test_invalid_artifact_one_repair_then_fail(client,login):
    login(client);pid=create(client,'[mock:invalid]');finish();s=snapshot(client,pid)
    assert s['run']['status']=='failed' and not s['build'];assert len([e for e in s['run']['events'] if '修复' in e['detail']])==2

def test_concurrency_gate_and_retry_message_not_duplicated(client,login):
    login(client);pid=create(client,'[mock:fail]')
    assert generate(client,pid,'another').status_code==409;finish()
    previous=snapshot(client,pid)['run'];config=configuration(client);key=str(uuid.uuid4())
    body={'idempotency_key':key,'config_id':config['id'],'config_version':config['version']}
    a=client.post(f'/api/projects/{pid}/runs/{previous["id"]}/retry',json=body);b=client.post(f'/api/projects/{pid}/runs/{previous["id"]}/retry',json=body)
    assert a.status_code==202 and a.json()['id']==b.json()['id']
    with SessionLocal() as db:assert db.scalar(select(func.count()).select_from(Message).where(Message.role=='user'))==1

def test_queued_stop_and_late_worker_no_activation(client,login):
    login(client);pid=create(client);job=maintenance_and_claim();run=snapshot(client,pid)['run']
    assert client.post(f'/api/projects/{pid}/runs/{run["id"]}/stop').status_code==200
    asyncio.run(execute(*job));assert snapshot(client,pid)['run']['status']=='cancelled';assert not snapshot(client,pid)['build']

def test_delete_cancels_jobs_clears_key_and_gate(client,login):
    login(client);pid=create(client);job=maintenance_and_claim()
    assert client.post('/api/model-config/delete',json={'confirm':True}).status_code==200
    asyncio.run(execute(*job));assert snapshot(client,pid)['run']['status']=='cancelled'
    with SessionLocal() as db:
        c=db.scalar(select(ModelConfiguration));assert c.ciphertext is None and c.deleted_at and not c.enabled
    assert client.get('/api/model-config').json()['config'] is None

def test_active_job_blocks_config_replacement(client,login):
    login(client);create(client)
    r=client.post('/api/model-config/test',json={'provider':'mock','api_key':'','base_url':'mock://local','model':'changed','idempotency_key':str(uuid.uuid4()),'consent':True})
    assert r.status_code==409

def test_logout_does_not_cancel_backend(client,login):
    login(client);pid=create(client);client.post('/api/auth/logout');finish()
    with SessionLocal() as db:
        assert db.scalar(select(GenerationRun)).status=='succeeded';assert db.get(Project,pid).current_build_id

def test_stale_worker_lease_no_charge_replay(client,login):
    login(client);pid=create(client);job=maintenance_and_claim()
    with SessionLocal() as db:db.get(GenerationRun,job[0]).lease_expires_at=now()-timedelta(seconds=1);db.commit()
    assert maintenance_and_claim() is None
    asyncio.run(execute(*job));assert snapshot(client,pid)['run']['status']=='interrupted';assert not snapshot(client,pid)['build']

@pytest.mark.parametrize('url',['http://127.0.0.1','https://u:p@api.openai.com/v1','https://api.openai.com/v1?key=x','https://api.openai.com:444/v1','https://169.254.169.254'])
def test_ssrf_url_rejection(url):
    with pytest.raises(ProviderError):resolve_target(url)

def test_dns_pin_rejects_any_private_address():
    with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
        with pytest.raises(ProviderError):resolve_target('https://api.openai.com/v1')
    with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443))]):
        url,host=resolve_target('https://api.openai.com/v1');assert url=='https://8.8.8.8/v1/chat/completions' and host=='api.openai.com'

def test_production_mock_fail_closed():
    with pytest.raises(ValueError):Settings(_env_file=None,app_env='production',dev_mock_auth=True,mail_mode='disabled')
    with pytest.raises(ValueError):Settings(_env_file=None,app_env='production',dev_mock_model=True,mail_mode='disabled')

def test_isolated_preview_signature_and_public_api_absence(client,login):
    login(client);pid=create(client);finish();bid=snapshot(client,pid)['build']['id'];url=preview_url(pid,bid)
    from urllib.parse import urlsplit
    p=urlsplit(url)
    with TestClient(isolated,base_url='http://'+p.netloc) as appclient:
        assert appclient.get('/').status_code==404
        r=appclient.get('/?'+p.query);assert r.status_code==200 and 'sandbox' in r.headers['content-security-policy']
        assert appclient.get('/api/auth/me').status_code==404

def test_mock_session_disallowed_after_toggle(client,monkeypatch):
    monkeypatch.setattr(settings,'dev_mock_auth',True)
    assert client.post('/api/dev/mock-login',json={'account':'bob'}).status_code==200
    monkeypatch.setattr(settings,'dev_mock_auth',False)
    assert client.get('/api/auth/me').status_code==401

def test_stale_config_version_rejected(client,login):
    login(client);pid=create(client);finish();config=configuration(client)
    r=client.post(f'/api/projects/{pid}/generate',json={'prompt':'a','idempotency_key':str(uuid.uuid4()),'config_id':config['id'],'config_version':config['version']+1,'base_build_id':snapshot(client,pid)['build']['id']})
    assert r.status_code==409

def test_model_draft_idempotency_no_repeat(client,login):
    login(client);key=str(uuid.uuid4());body={'provider':'mock','api_key':'','base_url':'mock://local','model':'changed','idempotency_key':key,'consent':True}
    a=client.post('/api/model-config/test',json=body);b=client.post('/api/model-config/test',json=body)
    assert a.json()['draft_id']==b.json()['draft_id']

def test_budget_timeout_preserves_previous(client,login,monkeypatch):
    login(client);pid=create(client);finish();old=snapshot(client,pid)['build']['id']
    monkeypatch.setattr(settings,'run_budget_seconds',0.05);generate(client,pid,'[mock:slow]');finish()
    assert snapshot(client,pid)['run']['status']=='failed' and snapshot(client,pid)['build']['id']==old

def test_save_retry_no_new_model_request(client,login):
    from app.worker import commit_candidate
    login(client);pid=create(client);run=snapshot(client,pid)['run']
    html=(Path(__file__).resolve().parents[1]/'app/fixtures/tasks.html').read_text()
    with SessionLocal() as db:
        r=db.get(GenerationRun,run['id']);r.status='save_failed';r.candidate={'html':html,'validation':validate_html(html),'mock':True};db.commit()
    response=client.post(f'/api/projects/{pid}/runs/{run["id"]}/retry-save')
    assert response.status_code==200 and snapshot(client,pid)['build']
    with SessionLocal() as db:assert db.scalar(select(func.count()).select_from(GenerationRun))==1

def test_publication_verified_update_and_failure_rollback(client,login,monkeypatch):
    import httpx
    from app.api.publication import process_publication
    login(client);pid=create(client);finish();old=snapshot(client,pid)['build']['id']
    key=str(uuid.uuid4());body={'build_id':old,'idempotency_key':key}
    assert client.post(f'/api/projects/{pid}/publish',json=body).status_code==202
    assert client.post(f'/api/projects/{pid}/publish',json=body).status_code==202
    class LocalClient:
        def __init__(self,*args,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def get(self,url,headers):
            from urllib.parse import urlsplit
            with TestClient(isolated,base_url='http://'+headers['Host']) as service:
                return service.get(urlsplit(url).path+'?'+urlsplit(url).query)
    monkeypatch.setattr(httpx,'AsyncClient',LocalClient)
    assert asyncio.run(process_publication())
    first=client.get(f'/api/projects/{pid}/publication').json();assert first['status']=='published' and first['published_build_id']==old
    generate(client,pid,'主色改紫');finish();new=snapshot(client,pid)['build']['id']
    assert client.post(f'/api/projects/{pid}/publish',json={'build_id':new,'idempotency_key':str(uuid.uuid4())}).status_code==202
    class BrokenClient(LocalClient):
        async def get(self,*args,**kwargs):raise OSError()
    monkeypatch.setattr(httpx,'AsyncClient',BrokenClient);asyncio.run(process_publication())
    result=client.get(f'/api/projects/{pid}/publication').json();assert result['status']=='failed' and result['published_build_id']==old and result['url']==first['url']

def test_artifact_validation_rejects_network_and_syntax():
    with pytest.raises(ProviderError):validate_html('<!doctype html><html><body><script src="https://evil.example/x.js"></script></body></html>')
    with pytest.raises(ProviderError):validate_html('<!doctype html><html><body><script>let x=;</script></body></html>')
