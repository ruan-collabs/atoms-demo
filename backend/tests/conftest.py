import os
import atexit
import sys
import subprocess
import uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import psycopg
from psycopg import sql
import pytest

# Tests may ONLY create a temporary database on the project's loopback PostgreSQL.
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'backend'))
admin_url = os.environ.get('ATOMS_TEST_ADMIN_URL', 'postgresql://atoms@127.0.0.1:55432/postgres')
parsed = urlsplit(admin_url)
if parsed.hostname not in ('localhost', '127.0.0.1'):
    raise RuntimeError('Tests are restricted to loopback PostgreSQL; refusing remote database')
db_name = 'atoms_test_' + uuid.uuid4().hex[:12]
with psycopg.connect(admin_url, autocommit=True) as conn:
    conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db_name)))
def cleanup_test_database():
    from app.db import engine
    engine.dispose()
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(db_name)))

atexit.register(cleanup_test_database)
os.environ['DATABASE_URL'] = urlunsplit(parsed._replace(path='/' + db_name))
os.environ['APP_ENV'] = 'test'
os.environ['MAIL_MODE'] = 'file'
os.environ['PUBLIC_ORIGIN'] = 'http://localhost:5173'
os.environ['GOOGLE_CLIENT_ID'] = ''
os.environ['GOOGLE_CLIENT_SECRET'] = ''
os.environ['DEV_MOCK_AUTH'] = 'true'
os.environ['DEV_MOCK_MODEL'] = 'true'
os.environ['CREDENTIAL_MASTER_KEY'] = __import__('base64').urlsafe_b64encode(os.urandom(32)).decode()
subprocess.run([str(root/'backend/.venv/bin/alembic'), '-c', str(root/'backend/alembic.ini'), 'upgrade', 'head'], check=True, cwd=root)

from fastapi.testclient import TestClient
from sqlalchemy import text
from app.db import engine
from app.main import app
from app.api import auth

@pytest.fixture(scope='session', autouse=True)
def test_database():
    yield
    cleanup_test_database()
    atexit.unregister(cleanup_test_database)

@pytest.fixture(autouse=True)
def reset_test_data():
    with engine.begin() as conn:
        conn.execute(text('TRUNCATE users, rate_limits, login_challenges, oauth_challenges, service_heartbeats CASCADE'))

@pytest.fixture
def mailbox(monkeypatch):
    items = []
    monkeypatch.setattr(auth, 'send_code', lambda email, code: items.append((email, code)))
    return items

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
def login(mailbox):
    def login_user(client, email='alice@example.com'):
        result = client.post('/api/auth/email/code', json={'email': email, 'terms_accepted': True})
        assert result.status_code == 202, result.text
        challenge = result.json()['challenge_id']
        response = client.post('/api/auth/email/verify', json={'challenge_id': challenge, 'code': mailbox[-1][1]})
        assert response.status_code == 200, response.text
        client.headers['X-CSRF-Token'] = response.json()['csrf_token']
        # Auth tests also prepare an explicit development-only model fixture for project APIs.
        draft=client.post('/api/model-config/test',json={'provider':'mock','api_key':'','base_url':'mock://local','model':'fixture','idempotency_key':str(uuid.uuid4()),'consent':True})
        assert draft.status_code==200,draft.text
        assert client.post('/api/model-config/save',json={'draft_id':draft.json()['draft_id'],'consent':True}).status_code==200
        from app.services.readiness import heartbeat
        heartbeat(str(uuid.uuid4()),'worker')
        return response.json()['user']
    return login_user
