import asyncio
import pytest
from sqlalchemy import select
from app import worker
from app.config import settings
from app.db import SessionLocal
from app.models import ModelConfiguration,GenerationRun
from app.services.credentials import encrypt
from app.services.provider import ProviderError
from test_generation import create,snapshot

HTML='<!doctype html><html><head></head><body><script>async function save(){await atomsStorage.setItem("atoms-app:data:v1",JSON.stringify([]));}</script></body></html>'

def prepare(client,login,monkeypatch):
 login(client);monkeypatch.setattr(settings,'application_sandbox',True)
 with SessionLocal() as db:
  c=db.scalar(select(ModelConfiguration));c.provider='deepseek';c.base_url='https://api.deepseek.com';c.model='deepseek-flash';c.ciphertext=encrypt('fixture-only-key',c.owner_id,c.id,c.version);db.commit()
 plans=[]
 async def plan(config,key,messages,**kwargs):plans.append(messages);return '{"scope":"local notes","storage":"atomsStorage"}'
 monkeypatch.setattr(worker,'completion',plan)
 async def no_backoff(_):return None
 monkeypatch.setattr(worker,'retry_delay',no_backoff)
 return plans


def test_length_retry_success_same_run_no_replan(client,login,monkeypatch):
 plans=prepare(client,login,monkeypatch);limits=[]
 async def stream(config,key,messages,on_delta,**kwargs):
  limits.append(kwargs['max_tokens'])
  if len(limits)==1:await on_delta('partial '*100);raise ProviderError('length','truncated',finish_reason='length',received_bytes=700)
  await on_delta(HTML);return HTML
 monkeypatch.setattr(worker,'stream_completion',stream)
 pid=create(client,'notes');job=worker.maintenance_and_claim();asyncio.run(worker.execute(*job));snap=snapshot(client,pid)
 assert snap['run']['status']=='succeeded' and limits==[16384,32768] and len(plans)==1
 assert 'atomsStorage' in plans[0][0]['content']
 with SessionLocal() as db:
  r=db.get(GenerationRun,job[0]);assert r.stream_text==HTML and r.stream_revision==2
 assert [e['auto_retry'] for e in snap['run']['events'] if e.get('auto_retry')]==[1]


def test_three_retries_maximum(client,login,monkeypatch):
 prepare(client,login,monkeypatch);calls=[]
 async def stream(*args,**kwargs):calls.append(1);raise ProviderError('length','truncated',finish_reason='length')
 monkeypatch.setattr(worker,'stream_completion',stream)
 pid=create(client);asyncio.run(worker.execute(*worker.maintenance_and_claim()));snap=snapshot(client,pid)
 assert len(calls)==4 and snap['run']['status']=='failed' and snap['build'] is None
 assert [e['auto_retry'] for e in snap['run']['events'] if e.get('auto_retry')]==[1,2,3]


@pytest.mark.parametrize('category',['auth','balance','refusal','leak','destination','timeout','network'])
def test_nonretryable_never_replayed(client,login,monkeypatch,category):
 prepare(client,login,monkeypatch);calls=[]
 async def stream(*args,**kwargs):calls.append(1);raise ProviderError('fixture failure',category)
 monkeypatch.setattr(worker,'stream_completion',stream)
 pid=create(client);asyncio.run(worker.execute(*worker.maintenance_and_claim()))
 assert len(calls)==1 and snapshot(client,pid)['run']['status']=='failed'


def test_planning_and_generation_share_retry_budget(client,login,monkeypatch):
 prepare(client,login,monkeypatch);plans=[];calls=[]
 async def plan(*args,**kwargs):
  plans.append(1)
  if len(plans)<=2:raise ProviderError('busy','http_retry',http_status=503)
  return '{"scope":"notes"}'
 async def stream(*args,**kwargs):calls.append(1);raise ProviderError('length','truncated')
 monkeypatch.setattr(worker,'completion',plan);monkeypatch.setattr(worker,'stream_completion',stream)
 pid=create(client);asyncio.run(worker.execute(*worker.maintenance_and_claim()));snap=snapshot(client,pid)
 assert len(plans)==3 and len(calls)==2
 assert [e['auto_retry'] for e in snap['run']['events'] if e.get('auto_retry')]==[1,2,3]


@pytest.mark.parametrize('change',['cancel','budget'])
def test_backoff_stop_or_budget_prevents_next_call(client,login,monkeypatch,change):
 prepare(client,login,monkeypatch);calls=[]
 async def stream(*args,**kwargs):calls.append(1);raise ProviderError('length','truncated')
 async def stop(_):
  if change=='budget':raise TimeoutError()
  with SessionLocal() as db:r=db.scalar(select(GenerationRun));r.status='cancelling';db.commit()
 monkeypatch.setattr(worker,'stream_completion',stream);monkeypatch.setattr(worker,'retry_delay',stop)
 pid=create(client);asyncio.run(worker.execute(*worker.maintenance_and_claim()))
 assert len(calls)==1 and snapshot(client,pid)['run']['status']==('cancelled' if change=='cancel' else 'failed')


def test_delete_during_backoff_prevents_next_call(client,login,monkeypatch):
 prepare(client,login,monkeypatch);calls=[]
 async def stream(*args,**kwargs):calls.append(1);raise ProviderError('length','truncated')
 async def delete_config(_):
  with SessionLocal() as db:c=db.scalar(select(ModelConfiguration));c.enabled=False;c.ciphertext=None;db.commit()
 monkeypatch.setattr(worker,'stream_completion',stream);monkeypatch.setattr(worker,'retry_delay',delete_config)
 pid=create(client);asyncio.run(worker.execute(*worker.maintenance_and_claim()))
 assert len(calls)==1 and snapshot(client,pid)['run']['status']=='cancelled'
