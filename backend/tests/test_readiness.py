import asyncio
import uuid
from datetime import timedelta
from sqlalchemy import select, delete
from app.db import SessionLocal
from app.models import GenerationRun, ModelConfiguration, ServiceHeartbeat, now
from app.services.readiness import heartbeat
from app.worker import maintenance_and_claim, execute
from test_generation import create, snapshot, configuration


def test_unready_preserves_no_project_no_model_call(client,login):
    login(client)
    with SessionLocal() as db:db.execute(delete(ServiceHeartbeat));db.commit()
    response=client.post('/api/projects',json={'prompt':'test','idempotency_key':str(uuid.uuid4())})
    assert response.status_code==503
    assert client.get('/api/projects').json()['total']==0
    assert client.get('/api/projects/generation/service-status').json()['can_generate'] is False


def test_legacy_real_queue_manual_retry_only(client,login):
    login(client);pid=create(client)
    with SessionLocal() as db:
        run=db.scalar(select(GenerationRun));run.provider='deepseek';run.dispatch_version=0;db.commit()
    assert maintenance_and_claim() is None
    assert snapshot(client,pid)['run']['requires_resubmit']
    config=configuration(client);run=snapshot(client,pid)['run']
    response=client.post(f'/api/projects/{pid}/runs/{run["id"]}/retry',json={'idempotency_key':str(uuid.uuid4()),'config_id':config['id'],'config_version':config['version']})
    assert response.status_code==202
    with SessionLocal() as db:
        assert db.get(GenerationRun,run['id']).status=='cancelled'
        assert db.get(GenerationRun,response.json()['id']).dispatch_version==1


def test_mock_heartbeat_not_real_readiness(client,login):
    login(client)
    with SessionLocal() as db:
        db.execute(delete(ServiceHeartbeat));c=db.scalar(select(ModelConfiguration));c.provider='deepseek';db.commit()
    heartbeat(str(uuid.uuid4()),'worker',True)
    assert client.get('/api/projects/generation/service-status').json()['worker_ready'] is False
    real=str(uuid.uuid4());heartbeat(real,'worker',False)
    assert client.get('/api/projects/generation/service-status').json()['worker_ready'] is True
    with SessionLocal() as db:db.get(ServiceHeartbeat,real).seen_at=now()-timedelta(seconds=30);db.commit()
    assert client.get('/api/projects/generation/service-status').json()['worker_ready'] is False


def test_stream_resume_reset_and_owner_isolation(client,login):
    login(client);pid=create(client);job=maintenance_and_claim();asyncio.run(execute(*job))
    rid=snapshot(client,pid)['run']['id']
    first=client.get(f'/api/projects/{pid}/runs/{rid}/stream').json()
    assert first['delta'].startswith('<!DOCTYPE html') or first['delta'].lower().startswith('<!doctype html')
    second=client.get(f'/api/projects/{pid}/runs/{rid}/stream?offset={first["next_offset"]}&revision={first["revision"]}').json()
    assert second['delta']==''
    with SessionLocal() as db:
        run=db.get(GenerationRun,rid);run.stream_revision+=1;run.stream_text='new';db.commit()
    reset=client.get(f'/api/projects/{pid}/runs/{rid}/stream?offset=2&revision={first["revision"]}').json()
    assert reset['reset'] and reset['offset']==0 and reset['delta']=='new'
    login(client,'bob@example.com')
    assert client.get(f'/api/projects/{pid}/runs/{rid}/stream').status_code==404


def test_real_dispatch_uses_stream_callback_and_saves(client,login,monkeypatch):
    from app import worker
    from app.services.credentials import encrypt
    login(client)
    with SessionLocal() as db:
        config=db.scalar(select(ModelConfiguration));config.provider='deepseek';config.base_url='https://api.deepseek.com';config.model='deepseek-flash'
        config.ciphertext=encrypt('fixture-only-key',config.owner_id,config.id,config.version);db.commit()
    async def plan(*args,**kwargs):return '{"scope":"local app","components":["form"]}'
    html='<!doctype html><html><head><title>Flow</title></head><body><button onclick="this.textContent=1">0</button></body></html>'
    called=[]
    async def stream(config,key,messages,on_delta,**kwargs):
        called.append(True);assert key=='fixture-only-key'
        await on_delta(html[:80]);await on_delta(html[80:]);return html
    monkeypatch.setattr(worker,'completion',plan);monkeypatch.setattr(worker,'stream_completion',stream)
    pid=create(client);job=maintenance_and_claim();asyncio.run(execute(*job))
    snap=snapshot(client,pid)
    assert called==[True] and snap['run']['status']=='succeeded' and not snap['build']['mock']
    with SessionLocal() as db:
        run=db.get(GenerationRun,job[0]);assert run.stream_text==html and run.stream_bytes==len(html.encode())


def test_preview_and_publication_readiness_separate(client,login):
    login(client);heartbeat(str(uuid.uuid4()),'application')
    state=client.get('/api/projects/generation/service-status').json()
    assert state['preview_ready'] and not state['publication_ready']
    heartbeat(str(uuid.uuid4()),'publication')
    assert client.get('/api/projects/generation/service-status').json()['publication_ready']
