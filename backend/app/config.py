from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    app_env: Literal['development', 'test', 'production'] = 'development'
    database_url: str = 'postgresql://atoms:atoms@127.0.0.1:5432/atoms'
    app_secret: str = 'development-only-change-before-deploy'
    public_origin: str = 'http://localhost:5173'
    mail_mode: Literal['file', 'smtp', 'disabled'] = 'file'
    mail_from: str = 'Atoms Demo <noreply@example.com>'
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_user: str = ''
    smtp_password: str = ''
    smtp_security: Literal['starttls', 'ssl'] = 'starttls'
    dev_mailbox_path: str = str(ROOT / '.runtime' / 'mailbox.jsonl')
    session_days: int = 7
    model_allowed_origins: str = 'https://api.openai.com,https://api.deepseek.com'
    frontend_dist: str = str(ROOT / 'frontend' / 'dist')
    google_client_id: str = ''
    google_client_secret: str = ''
    dev_mock_auth: bool = False
    dev_mock_model: bool = False
    dev_inline_worker: bool = False
    dev_mock_sandbox: bool = False
    credential_master_key: str = ''
    credential_key_file: str = str(ROOT / '.runtime' / 'credential.key')
    preview_origin: str = 'http://localhost:8001'
    app_origin: str = 'http://localhost:8002'
    worker_poll_seconds: float = 0.5
    run_budget_seconds: int = 180
    lease_seconds: int = 60
    mock_delay_seconds: float = 1.0
    voice_enabled: bool = False
    voice_provider: Literal['deepgram', 'volcengine'] = 'deepgram'
    volc_asr_api_key: str = ''
    volc_asr_resource_id: str = ''
    deepgram_api_key: str = ''
    voice_model: str = 'nova-2'
    voice_language: str = 'zh-CN'
    voice_max_seconds: int = 60
    voice_max_connections: int = 2

    @property
    def voice_configured(self):
        if self.voice_provider == 'volcengine':
            return bool(self.volc_asr_api_key and self.volc_asr_resource_id in (
                'volc.bigasr.sauc.duration', 'volc.bigasr.sauc.concurrent',
                'volc.seedasr.sauc.duration', 'volc.seedasr.sauc.concurrent'))
        return bool(self.deepgram_api_key)

    @property
    def mock_allowed(self):
        return not self.production

    def app_url(self, project_id: str, public=False):
        from urllib.parse import urlunsplit
        origin = urlsplit(self.app_origin if public else self.preview_origin)
        host = f"{'a' if public else 'p'}-{project_id}.{origin.hostname}"
        return urlunsplit((origin.scheme, host + (f':{origin.port}' if origin.port else ''), '/', '', ''))

    @property
    def google_enabled(self):
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def google_redirect_uri(self):
        return self.public_origin + '/api/auth/google/callback'

    @property
    def secure_cookies(self):
        return self.production or urlsplit(self.public_origin).scheme == 'https'

    @property
    def production(self):
        return self.app_env == 'production'

    @property
    def db_url(self):
        url = self.database_url
        if url.startswith('postgres://'):
            url = 'postgresql://' + url[len('postgres://'):]
        if url.startswith('postgresql://'):
            url = 'postgresql+psycopg://' + url[len('postgresql://'):]
        if not url.startswith('postgresql+psycopg://'):
            raise ValueError('Only PostgreSQL with psycopg is supported')
        return url

    @property
    def allowed_model_origins(self):
        return [x.strip() for x in self.model_allowed_origins.split(',') if x.strip()]

    @model_validator(mode='after')
    def secure_production(self):
        if bool(self.google_client_id) != bool(self.google_client_secret):
            raise ValueError('Google OAuth requires both GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET')
        if self.google_enabled:
            parts = urlsplit(self.public_origin)
            if parts.scheme == 'https' and (len(self.app_secret) < 32 or self.app_secret.startswith('development')):
                raise ValueError('HTTPS Google OAuth requires a stable random APP_SECRET of at least 32 characters')
            if not parts.netloc or parts.username or parts.password or parts.path or parts.query or parts.fragment:
                raise ValueError('Google OAuth requires exact PUBLIC_ORIGIN without trailing slash')
            if parts.scheme != 'https' and not (not self.production and parts.scheme == 'http' and parts.hostname in ('localhost', '127.0.0.1')):
                raise ValueError('OAuth callback requires HTTPS or development loopback')
        for origin in self.allowed_model_origins:
            parts = urlsplit(origin)
            if parts.scheme != 'https' or not parts.netloc or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ('', '/'):
                raise ValueError('MODEL_ALLOWED_ORIGINS must contain exact HTTPS origins')
        if self.production:
            if self.dev_mock_auth or self.dev_mock_model or self.dev_inline_worker or self.dev_mock_sandbox:
                raise ValueError('All development mocks are forbidden in production')
            if not self.credential_master_key:
                raise ValueError('Production requires separate CREDENTIAL_MASTER_KEY secret')
            import base64
            try:
                if len(base64.urlsafe_b64decode(self.credential_master_key))!=32:raise ValueError()
            except Exception:raise ValueError('CREDENTIAL_MASTER_KEY must be base64 of 32 random bytes') from None
            for app_origin in (self.preview_origin, self.app_origin):
                origin = urlsplit(app_origin)
                if origin.scheme != 'https' or not origin.hostname or origin.hostname == urlsplit(self.public_origin).hostname or origin.path or origin.query or origin.fragment or origin.username or origin.password or origin.port not in (None,443):
                    raise ValueError('Production requires separate HTTPS preview/application wildcard origins')
            if self.preview_origin == self.app_origin:
                raise ValueError('Preview and publication origins must be separate')
            if len(self.app_secret) < 32 or self.app_secret.startswith('development'):
                raise ValueError('Production requires a random APP_SECRET of at least 32 characters')
            parts = urlsplit(self.public_origin)
            if parts.scheme != 'https' or not parts.netloc or parts.username or parts.password or parts.path or parts.query or parts.fragment:
                raise ValueError('Production requires an exact HTTPS PUBLIC_ORIGIN without trailing slash')
            if self.mail_mode == 'file':
                raise ValueError('Development mailbox is forbidden in production')
            if self.mail_mode == 'smtp' and (not self.smtp_host or not self.smtp_user or not self.smtp_password):
                raise ValueError('SMTP credentials required')
        return self

settings = Settings()
