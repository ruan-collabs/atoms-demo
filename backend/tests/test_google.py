import base64
import hashlib
import time
from urllib.parse import parse_qs, urlsplit
from datetime import timedelta
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select, func
from app.config import settings
from app.db import SessionLocal
from app.models import OAuthChallenge, OAuthIdentity, User, Workspace, now
from app.security import digest
from app.services import google

@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings,'google_client_id','fixture.apps.googleusercontent.com')
    monkeypatch.setattr(settings,'google_client_secret','test-only-placeholder')

def start(client):
    r=client.post('/api/auth/google/start',json={'terms_accepted':True})
    assert r.status_code==200,r.text
    return parse_qs(urlsplit(r.json()['authorization_url']).query)

def fake_google(monkeypatch,sub='google-fixture-user',email='google@example.com'):
    async def exchange(code,verifier):
        return 'test-id-token'
    monkeypatch.setattr(google,'exchange_code',exchange)
    monkeypatch.setattr(google,'validate_id_token',lambda token,nonce_hash:{'sub':sub,'email':email})

def test_google_disabled_is_explicit(client,monkeypatch):
    monkeypatch.setattr(settings,'google_client_id','')
    monkeypatch.setattr(settings,'google_client_secret','')
    assert client.post('/api/auth/google/start',json={'terms_accepted':True}).status_code==503
    assert client.get('/api/meta').json()['features']['google_login'] is False

def test_google_requires_terms(client,enabled):
    assert client.post('/api/auth/google/start',json={'terms_accepted':False}).status_code==422

def test_google_authorization_state_pkce_callback(client,enabled):
    query=start(client)
    assert query['redirect_uri']==['http://localhost:5173/api/auth/google/callback']
    assert query['scope']==['openid email']
    assert query['code_challenge_method']==['S256']
    verifier=client.cookies.get('atoms_oauth_verifier')
    expected=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    assert query['code_challenge']==[expected]
    with SessionLocal() as db:
        challenge=db.get(OAuthChallenge,digest(query['state'][0]))
        assert challenge.nonce_hash==digest(query['nonce'][0])
        assert db.scalar(select(func.count()).select_from(User))==0

def test_google_bad_state_or_missing_cookie_rejected(client,enabled):
    query=start(client)
    r=client.get('/api/auth/google/callback?state=wrong&code=test',follow_redirects=False)
    assert 'invalid_state' in r.headers['location']
    client.cookies.clear()
    r=client.get('/api/auth/google/callback',params={'state':query['state'][0],'code':'test'},follow_redirects=False)
    assert 'invalid_state' in r.headers['location']
    assert client.get('/api/auth/me').status_code==401

def test_google_expired_state(client,enabled):
    query=start(client)
    with SessionLocal() as db:
        db.get(OAuthChallenge,digest(query['state'][0])).expires_at=now()-timedelta(seconds=1);db.commit()
    r=client.get('/api/auth/google/callback',params={'state':query['state'][0],'code':'test'},follow_redirects=False)
    assert 'invalid_state' in r.headers['location']

def test_google_cancel_consumes_state(client,enabled):
    query=start(client)
    r=client.get('/api/auth/google/callback',params={'state':query['state'][0],'error':'access_denied'},follow_redirects=False)
    assert 'google_cancelled' in r.headers['location']
    assert client.get('/api/auth/me').status_code==401
    with SessionLocal() as db:
        assert db.get(OAuthChallenge,digest(query['state'][0])).consumed_at

def test_google_success_mapping_cookie_replay(client,enabled,monkeypatch):
    fake_google(monkeypatch)
    query=start(client)
    r=client.get('/api/auth/google/callback',params={'state':query['state'][0],'code':'test'},follow_redirects=False)
    assert r.status_code==303 and r.headers['location']=='http://localhost:5173/dashboard'
    assert 'httponly' in r.headers['set-cookie'].lower()
    assert 'test-id-token' not in r.text+r.headers['location']
    user=client.get('/api/auth/me').json()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(User))==1
        assert db.scalar(select(func.count()).select_from(Workspace))==1
        assert db.scalar(select(OAuthIdentity)).user_id==user['id']
    replay=client.get('/api/auth/google/callback',params={'state':query['state'][0],'code':'test'},follow_redirects=False)
    assert 'invalid_state' in replay.headers['location']

def test_google_same_subject_stable_account_when_email_changes(client,enabled,monkeypatch):
    fake_google(monkeypatch);query=start(client)
    client.get('/api/auth/google/callback',params={'state':query['state'][0],'code':'test'},follow_redirects=False)
    original=client.get('/api/auth/me').json()['id']
    fake_google(monkeypatch,email='new-google@example.com');query=start(client)
    client.get('/api/auth/google/callback',params={'state':query['state'][0],'code':'test'},follow_redirects=False)
    assert client.get('/api/auth/me').json()['id']==original
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(User))==1

def test_google_does_not_auto_merge_existing_email(client,enabled,login,monkeypatch):
    login(client,'google@example.com')
    csrf=client.headers['X-CSRF-Token'];client.post('/api/auth/logout')
    fake_google(monkeypatch);query=start(client)
    r=client.get('/api/auth/google/callback',params={'state':query['state'][0],'code':'test'},follow_redirects=False)
    assert 'account_exists' in r.headers['location']
    assert client.get('/api/auth/me').status_code==401
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(OAuthIdentity))==0

def test_google_exchange_failure_not_login(client,enabled,monkeypatch):
    async def failed(*args):raise google.GoogleAuthError('failed')
    monkeypatch.setattr(google,'exchange_code',failed);query=start(client)
    r=client.get('/api/auth/google/callback',params={'state':query['state'][0],'code':'test'},follow_redirects=False)
    assert 'google_failed' in r.headers['location']
    assert client.get('/api/auth/me').status_code==401

def test_google_https_development_cookies_are_secure(client,enabled,monkeypatch):
    monkeypatch.setattr(settings,'public_origin','https://demo.example.com')
    r=client.post('/api/auth/google/start',json={'terms_accepted':True})
    assert r.status_code==200
    assert '; secure' in r.headers['set-cookie'].lower()
    from app.api.auth import issue_session
    from fastapi import Response
    with SessionLocal() as db:
        user=User(email='secure-google@example.com');db.add(user);db.flush()
        response=Response();issue_session(db,user,response)
        assert '; secure' in response.headers['set-cookie'].lower()
        db.rollback()
    assert settings.secure_cookies is True
    monkeypatch.setattr(settings,'public_origin','http://localhost:5173')
    assert settings.secure_cookies is False

def test_google_exchange_uses_fixed_target_without_ambient_proxy(enabled,monkeypatch):
    seen={}
    class Reply:
        status_code=200
        def json(self):return {'id_token':'test-id-token'}
    class Client:
        def __init__(self,**kwargs):seen['options']=kwargs
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,url,**kwargs):seen['url']=url;seen['data']=kwargs['data'];return Reply()
    monkeypatch.setattr(google.httpx,'AsyncClient',Client)
    import asyncio
    assert asyncio.run(google.exchange_code('test-code','test-verifier'))=='test-id-token'
    assert seen['options']['trust_env'] is False
    assert seen['options']['follow_redirects'] is False
    assert seen['url']==google.TOKEN_URL
    assert seen['data']['code_verifier']=='test-verifier'
    assert seen['data']['redirect_uri']=='http://localhost:5173/api/auth/google/callback'

def test_google_https_refuses_default_session_secret():
    from app.config import Settings
    with pytest.raises(ValueError):
        Settings(_env_file=None,public_origin='https://demo.example.com',google_client_id='fixture.apps.googleusercontent.com',google_client_secret='test-only-placeholder')
    configured=Settings(_env_file=None,public_origin='https://demo.example.com',app_secret='x'*40,google_client_id='fixture.apps.googleusercontent.com',google_client_secret='test-only-placeholder')
    assert configured.secure_cookies

@pytest.fixture
def signing(monkeypatch,enabled):
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    class SigningKey:
        pass
    resolved=SigningKey();resolved.key=key.public_key()
    monkeypatch.setattr(google.jwks,'get_signing_key_from_jwt',lambda token:resolved)
    claims={'iss':'https://accounts.google.com','aud':settings.google_client_id,'sub':'verified-fixture','iat':int(time.time()),'exp':int(time.time())+300,'nonce':'nonce-fixture','email':'valid@example.com','email_verified':True}
    return key,claims

def test_google_id_token_signature_and_claims(signing):
    key,claims=signing
    token=jwt.encode(claims,key,algorithm='RS256',headers={'kid':'fixture'})
    assert google.validate_id_token(token,digest('nonce-fixture'))=={'sub':'verified-fixture','email':'valid@example.com'}

@pytest.mark.parametrize('field,value',[('aud','wrong-client'),('iss','https://evil.example'),('exp',1),('nonce','wrong'),('email_verified',False),('sub',''),('azp','wrong-client')])
def test_google_bad_signed_claims_rejected(signing,field,value):
    key,claims=signing;claims[field]=value
    token=jwt.encode(claims,key,algorithm='RS256',headers={'kid':'fixture'})
    with pytest.raises(google.GoogleAuthError):google.validate_id_token(token,digest('nonce-fixture'))

def test_google_invalid_signature_rejected(signing):
    key,claims=signing
    another=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    token=jwt.encode(claims,another,algorithm='RS256',headers={'kid':'fixture'})
    with pytest.raises(google.GoogleAuthError):google.validate_id_token(token,digest('nonce-fixture'))
