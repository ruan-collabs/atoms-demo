import asyncio,uuid
from sqlalchemy import select
from app.config import settings
from app.models import BuildArtifact
from app.db import SessionLocal
from app.worker import maintenance_and_claim,execute

def test_mock_sandbox_frame_is_opaque_owned_and_flag_gated(client,login,monkeypatch):
 monkeypatch.setattr(settings,'dev_mock_sandbox',True)
 monkeypatch.setattr(settings,'mock_delay_seconds',0.01)
 login(client)
 r=client.post('/api/projects',json={'prompt':'任务板','idempotency_key':str(uuid.uuid4())});pid=r.json()['id']
 asyncio.run(execute(*maintenance_and_claim()))
 path=f'/api/mock-sandbox/{pid}/frame?channel={uuid.uuid4()}'
 frame=client.get(path);assert frame.status_code==200
 csp=frame.headers['content-security-policy']
 assert 'sandbox allow-scripts allow-forms' in csp and 'allow-same-origin' not in csp
 assert frame.headers['permissions-policy']=='camera=(), microphone=(), geolocation=()'
 assert 'application/x-atoms-mock' in frame.text and 'mock-sandbox-child.js' in frame.text
 client.post('/api/auth/logout');assert client.get(path).status_code==401
 monkeypatch.setattr(settings,'dev_mock_sandbox',False);assert client.get(path).status_code==404

def test_mock_public_only_after_publish_and_is_verified_fixture(client,login,monkeypatch):
 monkeypatch.setattr(settings,'dev_mock_sandbox',True);monkeypatch.setattr(settings,'mock_delay_seconds',0.01)
 login(client)
 r=client.post('/api/projects',json={'prompt':'任务板','idempotency_key':str(uuid.uuid4())});pid=r.json()['id'];asyncio.run(execute(*maintenance_and_claim()))
 assert client.get(f'/api/mock-sandbox/{pid}/public').status_code==404
 build=client.get(f'/api/projects/{pid}/build').json()
 p=client.post(f'/api/projects/{pid}/publish',json={'build_id':build['id'],'idempotency_key':str(uuid.uuid4())})
 assert p.status_code==202 and p.json()['status']=='published' and '/mock-apps/' in p.json()['url']
 client.post('/api/auth/logout');assert client.get(f'/api/mock-sandbox/{pid}/public').status_code==200
 with SessionLocal() as db:
  b=db.get(BuildArtifact,build['id']);b.artifact={'html':'<html><script>evil()</script></html>','mock':True};db.commit()
 assert client.get(f'/api/mock-sandbox/{pid}/public').status_code==409
