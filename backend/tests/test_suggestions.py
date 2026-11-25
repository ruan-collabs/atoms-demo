import asyncio
import json
import uuid
import pytest
from sqlalchemy import select
from app import worker
from app.config import settings
from app.db import SessionLocal
from app.models import BuildArtifact, ModelConfiguration
from app.services.credentials import encrypt
from app.services.suggestions import clean_suggestions, suggestions_from_plan
from test_generation import create, snapshot, generate

SUGGESTIONS=[{'label':'增加归档','prompt':'增加笔记归档，保留现有数据。'},{'label':'优化标签展示','prompt':'优化标签展示，保留搜索与现有数据。'}]
HTML='<!doctype html><html><head></head><body><script>async function save(){await atomsStorage.setItem("atoms-app:data:v1",JSON.stringify([]));}</script></body></html>'

@pytest.mark.parametrize('value',[None,{},[],SUGGESTIONS[:1],SUGGESTIONS+[SUGGESTIONS[0]],[SUGGESTIONS[0],SUGGESTIONS[0]],[{'label':'x','prompt':'<script>'},SUGGESTIONS[1]],[{'label':'x','prompt':'https://example.com'},SUGGESTIONS[1]],[{'label':'x','prompt':'x'*401},SUGGESTIONS[1]]])
def test_invalid_metadata_is_omitted(value):assert clean_suggestions(value)==[]


def test_validation_and_no_secret_or_current_request():
 assert clean_suggestions(SUGGESTIONS)==SUGGESTIONS
 assert clean_suggestions(SUGGESTIONS,key='笔记归档')==[]
 assert clean_suggestions(SUGGESTIONS,current_prompt=SUGGESTIONS[0]['prompt'])==[]
 assert suggestions_from_plan('bad')==[]
 assert suggestions_from_plan('```json\n'+json.dumps({'suggestions':SUGGESTIONS})+'\n```')==SUGGESTIONS


def test_real_worker_reuses_planning_call_and_persists_per_build(client,login,monkeypatch):
 login(client);monkeypatch.setattr(settings,'application_sandbox',True)
 with SessionLocal() as db:
  c=db.scalar(select(ModelConfiguration));c.provider='deepseek';c.base_url='https://api.deepseek.com';c.model='deepseek-flash';c.ciphertext=encrypt('fixture-only-key',c.owner_id,c.id,c.version);db.commit()
 plans=[];codes=[]
 async def plan(config,key,messages,**kwargs):
  plans.append(messages)
  return json.dumps({'scope':'搜索笔记','storage':'atomsStorage','suggestions':SUGGESTIONS},ensure_ascii=False)
 async def stream(config,key,messages,on_delta,**kwargs):
  codes.append(messages);await on_delta(HTML);return HTML
 monkeypatch.setattr(worker,'completion',plan);monkeypatch.setattr(worker,'stream_completion',stream)
 pid=create(client,'灵感笔记');asyncio.run(worker.execute(*worker.maintenance_and_claim()))
 first=snapshot(client,pid);assert first['run']['status']=='succeeded';assert first['build']['suggestions']==SUGGESTIONS
 assert len(plans)==len(codes)==1
 assert 'suggestions must be exactly two' in plans[0][0]['content']
 assert all('增加笔记归档' not in m['content'] for m in codes[0])
 for _ in range(3):assert snapshot(client,pid)['build']['suggestions']==SUGGESTIONS
 assert len(plans)==1 # Readbacks never trigger paid requests.
 assert generate(client,pid,'增加搜索，保留现有数据').status_code==202
 asyncio.run(worker.execute(*worker.maintenance_and_claim()))
 second=snapshot(client,pid);assert second['build']['number']==2;assert second['build']['suggestions']==SUGGESTIONS
 assert 'existing_app_excerpt' in plans[1][1]['content'] and 'recent_requests' in plans[1][1]['content']
 assert 'previous_suggestions' in plans[1][1]['content'] and '增加搜索' in plans[1][-1]['content']
 assert len(plans)==2
 with SessionLocal() as db:
  old=db.get(BuildArtifact,first['build']['id']);assert old.artifact['suggestions']==SUGGESTIONS
  assert 'suggestions' not in old.artifact['html']


def test_legacy_and_mock_are_not_real_recommendations(client,login):
 login(client);pid=create(client,'个人作品集');asyncio.run(worker.execute(*worker.maintenance_and_claim()))
 snap=snapshot(client,pid);assert snap['build']['mock'];assert len(snap['build']['suggestions'])==2
 with SessionLocal() as db:
  build=db.get(BuildArtifact,snap['build']['id']);build.artifact={'html':build.artifact['html'],'mock':True};db.commit()
 assert snapshot(client,pid)['build']['suggestions']==[]
 assert client.get(f'/api/projects/{uuid.uuid4()}/snapshot').status_code==404
