import uuid
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.main import app
from app.config import Settings, settings
from app.db import SessionLocal
from app.models import LoginChallenge, User, Workspace, AuthSession, Project, Message, now


def create(client, prompt='创建任务管理应用', key=None):
    return client.post('/api/projects', json={'prompt':prompt,'idempotency_key':key or str(uuid.uuid4())})

def test_health_and_real_postgres(client):
    result=client.get('/api/health')
    assert result.status_code==200
    assert result.json()['database']=='postgresql'
    assert result.json()['migration']

def test_mail_request_no_user_before_verify(client,mailbox):
    response=client.post('/api/auth/email/code',json={'email':' Alice@example.com ','terms_accepted':True})
    assert response.status_code==202
    assert 'code' not in response.json()
    assert mailbox[0][0]=='alice@example.com'
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(User))==0
        challenge=db.get(LoginChallenge,response.json()['challenge_id'])
        assert challenge.code_hash != mailbox[0][1]

def test_wrong_code_and_five_attempt_lock(client,mailbox):
    challenge=client.post('/api/auth/email/code',json={'email':'a@example.com','terms_accepted':True}).json()['challenge_id']
    wrong='999999' if mailbox[0][1]!='999999' else '888888'
    for attempt in range(5):
        r=client.post('/api/auth/email/verify',json={'challenge_id':challenge,'code':wrong})
        assert r.status_code==(429 if attempt==4 else 400)
    assert client.post('/api/auth/email/verify',json={'challenge_id':challenge,'code':mailbox[0][1]}).status_code==429
    assert client.get('/api/auth/me').status_code==401

def test_expired_code(client,mailbox):
    cid=client.post('/api/auth/email/code',json={'email':'a@example.com','terms_accepted':True}).json()['challenge_id']
    with SessionLocal() as db:
        db.get(LoginChallenge,cid).expires_at=now()-timedelta(seconds=1);db.commit()
    assert client.post('/api/auth/email/verify',json={'challenge_id':cid,'code':mailbox[0][1]}).status_code==410

def test_resend_old_code_invalid_and_cooldown(client,mailbox):
    body={'email':'a@example.com','terms_accepted':True}
    cid=client.post('/api/auth/email/code',json=body).json()['challenge_id'];old=mailbox[0][1]
    assert client.post('/api/auth/email/code',json=body).status_code==429
    assert len(mailbox)==1
    with SessionLocal() as db:
        db.get(LoginChallenge,cid).created_at=now()-timedelta(seconds=61);db.commit()
    new=client.post('/api/auth/email/code',json=body)
    assert new.status_code==202
    assert new.json()['challenge_id']!=cid
    assert client.post('/api/auth/email/verify',json={'challenge_id':cid,'code':old}).status_code==400

def test_login_session_cookie_and_reuse_rejected(client,login,mailbox):
    user=login(client)
    assert client.get('/api/auth/me').json()['id']==user['id']
    with SessionLocal() as db:
        challenge=db.scalar(select(LoginChallenge))
        assert db.scalar(select(func.count()).select_from(User))==1
        assert db.scalar(select(func.count()).select_from(Workspace))==1
    assert client.post('/api/auth/email/verify',json={'challenge_id':challenge.id,'code':mailbox[0][1]}).status_code==400

def test_anonymous_routes_protected(client):
    assert client.get('/api/projects').status_code==401
    assert create(client).status_code==401

def test_csrf_and_origin(client,login):
    login(client)
    token=client.headers.pop('X-CSRF-Token')
    assert create(client).status_code==403
    client.headers['X-CSRF-Token']=token
    assert create(client).status_code==201
    assert client.post('/api/projects',headers={'Origin':'https://evil.example'},json={'prompt':'test','idempotency_key':str(uuid.uuid4())}).status_code==403

def test_csrf_stable_across_tab_refresh(client,login):
    login(client)
    token=client.headers['X-CSRF-Token']
    assert client.get('/api/auth/csrf').json()['csrf_token']==token
    assert client.get('/api/auth/csrf').json()['csrf_token']==token
    assert create(client).status_code==201

def test_project_atomic_idempotent_and_persistence(client,login):
    login(client)
    key=str(uuid.uuid4())
    a,b=create(client,key=key),create(client,key=key)
    assert a.status_code==b.status_code==201
    assert a.json()['id']==b.json()['id']
    assert create(client,prompt='different',key=key).status_code==409
    pid=a.json()['id']
    assert client.get('/api/projects').json()['total']==1
    assert len(client.get(f'/api/projects/{pid}/messages').json()['items'])==1
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Project))==1
        assert db.scalar(select(func.count()).select_from(Message))==1
        assert db.get(Project,pid).current_build_id is None

def test_rename_search_and_message_idempotency(client,login):
    login(client);pid=create(client).json()['id']
    assert client.patch(f'/api/projects/{pid}',json={'name':'新名字'}).status_code==200
    assert client.get('/api/projects?q=新名').json()['total']==1
    assert client.get('/api/projects?q=不存在').json()['total']==0
    body={'content':'主色改成紫色','idempotency_key':str(uuid.uuid4())}
    first=client.post(f'/api/projects/{pid}/messages',json=body)
    second=client.post(f'/api/projects/{pid}/messages',json=body)
    assert first.status_code==201 and first.json()==second.json()
    assert len(client.get(f'/api/projects/{pid}/messages').json()['items'])==2

def test_owner_isolation(client,login):
    login(client);pid=create(client).json()['id']
    with TestClient(app) as other:
        login(other,'bob@example.com')
        assert other.get('/api/projects').json()['total']==0
        assert other.get(f'/api/projects/{pid}').status_code==404
        assert other.get(f'/api/projects/{pid}/messages').status_code==404
        assert other.patch(f'/api/projects/{pid}',json={'name':'hack'}).status_code==404

def test_logout_revokes_server_session(client,login):
    login(client);saved=client.cookies.get('atoms_session')
    assert client.post('/api/auth/logout').status_code==204
    client.cookies.set('atoms_session',saved)
    assert client.get('/api/auth/me').status_code==401

def test_session_expiration(client,login):
    login(client)
    with SessionLocal() as db:
        db.scalar(select(AuthSession)).expires_at=now()-timedelta(seconds=1);db.commit()
    assert client.get('/api/projects').status_code==401

@pytest.mark.parametrize('prompt',['','   ','a'*4001])
def test_invalid_project_input(client,login,prompt):
    login(client);assert create(client,prompt=prompt).status_code==422
    assert client.get('/api/projects').json()['total']==0

def test_no_key_schema_and_unknown_api(client,login):
    login(client)
    assert client.post('/api/projects',json={'prompt':'a','idempotency_key':str(uuid.uuid4()),'api_key':'test-placeholder'}).status_code==422
    assert client.get('/api/missing').status_code==404
    assert client.get('/api/meta').json()['features']['generation'] is True
    assert client.get('/public/nonexistent').status_code==404

def test_mail_disabled_no_fake_success(client,monkeypatch):
    from app.api import auth
    from app.services import mail
    monkeypatch.setattr(auth,'send_code',mail.send_code)
    monkeypatch.setattr(settings,'mail_mode','disabled')
    assert client.post('/api/auth/email/code',json={'email':'a@example.com','terms_accepted':True}).status_code==503
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(LoginChallenge))==0

def test_production_guard_and_url_normalization():
    with pytest.raises(ValueError):
        Settings(_env_file=None,app_env='production',mail_mode='file')
    valid=Settings(_env_file=None,app_env='production',app_secret='x'*40,public_origin='https://atoms.example',mail_mode='disabled',credential_master_key=__import__('base64').urlsafe_b64encode(b'x'*32).decode(),dev_mock_auth=False,dev_mock_model=False,preview_origin='https://preview.example',app_origin='https://apps.example',database_url='postgres://a:b@localhost/atoms')
    assert valid.db_url=='postgresql+psycopg://a:b@localhost/atoms'
    assert valid.production

def test_concurrent_project_idempotency(client,login):
    login(client);key=str(uuid.uuid4())
    token=client.cookies.get('atoms_session');csrf=client.headers['X-CSRF-Token']
    def call(_):
        with TestClient(app) as tab:
            tab.cookies.set('atoms_session',token);tab.headers['X-CSRF-Token']=csrf
            return create(tab,key=key)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(call,range(2)))
    assert all(r.status_code==201 for r in results)
    assert len({r.json()['id'] for r in results})==1
    assert client.get('/api/projects').json()['total']==1
