"""Actual running-service smoke test using user-authorized development mocks."""
import json
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit
import httpx

root=Path(__file__).resolve().parents[1]
records=[]
with httpx.Client(base_url='http://127.0.0.1:8000',timeout=10,trust_env=False) as client:
    auth=client.post('/api/dev/mock-login',json={'account':'alice'});auth.raise_for_status()
    client.headers['X-CSRF-Token']=auth.json()['csrf_token']
    cfg=client.get('/api/model-config').json()['config'];assert cfg and cfg['mock']
    p=client.post('/api/projects',json={'prompt':'现场自动化验收：个人作品集','idempotency_key':str(uuid.uuid4()),'config_id':cfg['id'],'config_version':cfg['version']});p.raise_for_status();pid=p.json()['id']
    def wait_build():
        for _ in range(80):
            s=client.get(f'/api/projects/{pid}/snapshot').json()
            if s['run']['status']=='succeeded':return s
            if s['run']['status'] in ('failed','interrupted'):raise RuntimeError(s['run']['error'])
            time.sleep(.25)
        raise RuntimeError('Worker smoke timeout')
    first=wait_build();records.append({'check':'实际Worker首构建','result':'PASS','build':first['build']['number']})
    body={'build_id':first['build']['id'],'idempotency_key':str(uuid.uuid4())}
    client.post(f'/api/projects/{pid}/publish',json=body).raise_for_status()
    for _ in range(60):
        pub=client.get(f'/api/projects/{pid}/publication').json()
        if pub['status']=='published':break
        if pub['status']=='failed':raise RuntimeError(pub['error'])
        time.sleep(.25)
    assert pub['status']=='published'
    parts=urlsplit(pub['url']);r=httpx.get(f'http://127.0.0.1:{parts.port}/',headers={'Host':parts.netloc},trust_env=False)
    assert r.status_code==200 and '精选作品' in r.text and r.headers.get('X-Artifact-SHA256')
    records.append({'check':'实际预览/公开双可达核验与发布','result':'PASS','url':pub['url']})
    client.post(f'/api/projects/{pid}/generate',json={'prompt':'主色改紫','idempotency_key':str(uuid.uuid4()),'config_id':cfg['id'],'config_version':cfg['version'],'base_build_id':first['build']['id']}).raise_for_status()
    second=wait_build();assert second['build']['number']==2
    still=client.get(f'/api/projects/{pid}/publication').json();assert still['published_build_id']==first['build']['id']
    records.append({'check':'仅迭代线上旧版保留','result':'PASS'})
    client.post(f'/api/projects/{pid}/publish',json={'build_id':second['build']['id'],'idempotency_key':str(uuid.uuid4())}).raise_for_status()
    for _ in range(60):
        current=client.get(f'/api/projects/{pid}/publication').json()
        if current['status']=='published' and current['published_build_id']==second['build']['id']:break
        time.sleep(.25)
    assert current['published_build_id']==second['build']['id'] and current['url']==pub['url']
    r=httpx.get(f'http://127.0.0.1:{parts.port}/',headers={'Host':parts.netloc},trust_env=False);assert '--accent:#8b5cf6' in r.text
    records.append({'check':'稳定URL实际更新','result':'PASS'})
    client.post('/api/auth/logout').raise_for_status()
output=root/'docs/evidence/live-smoke.json';output.write_text(json.dumps({'mock':'仅身份与供应商响应，其余是真实运行服务','results':records},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(records,ensure_ascii=False))
