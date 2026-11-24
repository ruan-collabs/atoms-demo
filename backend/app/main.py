from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.config import settings
from app.db import engine
from app.api import auth, projects, google_auth, dev, model_config, generation, publication, voice, mock_sandbox, application_sandbox
from app.services.credentials import CredentialError
from app.services.provider import ProviderError

import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    task=None
    if settings.dev_inline_worker and not settings.production and settings.dev_mock_model:
        from app.worker import main as worker_main
        task=asyncio.create_task(worker_main(mock_only=True))
    try:yield
    finally:
        if task:
            task.cancel()
            await asyncio.gather(task,return_exceptions=True)

app = FastAPI(lifespan=lifespan,title='Atoms Demo API', version='0.2.0', docs_url='/api/docs' if not settings.production else None, openapi_url='/api/openapi.json' if not settings.production else None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=[settings.public_origin], allow_credentials=True,
                   allow_methods=['GET', 'POST', 'PATCH', 'OPTIONS'], allow_headers=['Content-Type', 'X-CSRF-Token'])

@app.middleware('http')
async def secure_headers(request: Request, call_next):
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and request.headers.get('origin') not in (None, settings.public_origin):
        return JSONResponse(status_code=403, content={'detail': '请求来源不受信任'})
    # Do not log bodies, credentials, or provider errors.
    response = await call_next(request)
    response.headers['X-Request-ID'] = str(uuid4())
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    if not request.url.path.startswith(('/api/mock-sandbox/','/api/application-sandbox/')):
        response.headers['X-Frame-Options'] = 'DENY'
    if not request.url.path.startswith(('/api/mock-sandbox/','/api/application-sandbox/')):
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(self), geolocation=()'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    else:
        connect = "'self' "+settings.public_origin.replace('https://','wss://').replace('http://','ws://')
        if not settings.production:
            connect += ' ws://localhost:5173 ws://127.0.0.1:5173'
        response.headers['Content-Security-Policy'] = f"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src {connect}; frame-src 'self' {settings.preview_origin.replace('://','://*.')}; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
    if settings.production:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response

@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    # Never echo invalid input: an accidental credential must not enter the error response.
    return JSONResponse(status_code=422, content={'detail': '输入不合法，请检查必填字段、长度和格式'})

@app.exception_handler(CredentialError)
async def encryption_error(request,exc):
    return JSONResponse(status_code=503,content={'detail':str(exc)})

@app.exception_handler(ProviderError)
async def provider_error(request,exc):
    return JSONResponse(status_code=422,content={'detail':str(exc)})

@app.exception_handler(SQLAlchemyError)
async def db_error(request, exc):
    return JSONResponse(status_code=503, content={'detail': '数据库暂不可用，请稍后重试'})

@app.get('/api/health', tags=['system'])
def health():
    try:
        with engine.connect() as db:
            db.execute(text('SELECT 1'))
            revision = db.scalar(text('SELECT version_num FROM alembic_version'))
        return {'status': 'ok', 'database': 'postgresql', 'migration': revision, 'version': '0.2.0'}
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={'status': 'unavailable', 'database': 'unavailable'})

@app.get('/api/meta', tags=['system'])
def meta():
    return {'version': '0.2.0', 'stage': 'V1.2构建平台', 'mail_mode': settings.mail_mode,
            'model_allowed_origins': settings.allowed_model_origins,
            'features': {'application_sandbox':settings.application_sandbox,'mock_auth':settings.dev_mock_auth and not settings.production,'mock_model':settings.dev_mock_model and not settings.production,'google_login': settings.google_enabled, 'projects': True, 'messages': True, 'model_connection_test': True, 'mock_sandbox':settings.dev_mock_sandbox and not settings.production, 'generation': True, 'preview': True, 'publication': True}}

app.include_router(auth.router, prefix='/api')
app.include_router(google_auth.router, prefix='/api')
app.include_router(projects.router, prefix='/api')
app.include_router(dev.router,prefix='/api')
app.include_router(model_config.router,prefix='/api')
app.include_router(generation.router,prefix='/api')
app.include_router(publication.router,prefix='/api')
app.include_router(voice.router,prefix='/api')
app.include_router(mock_sandbox.router,prefix='/api')
app.include_router(application_sandbox.router,prefix='/api')

@app.get('/mock-sandbox-child.js',include_in_schema=False)
def mock_sandbox_child():
    path=Path(settings.frontend_dist).resolve()/'mock-sandbox-child.js'
    if not path.is_file():return JSONResponse(status_code=404,content={'detail':'沙箱资源未构建'})
    response=FileResponse(path,media_type='application/javascript')
    response.headers['Access-Control-Allow-Origin']='*'
    return response

DIST = Path(settings.frontend_dist).resolve()
if (DIST / 'assets').is_dir():
    app.mount('/assets', StaticFiles(directory=DIST / 'assets'), name='assets')

@app.get('/voice-worklet.js', include_in_schema=False)
def voice_worklet():
    path=Path(settings.frontend_dist).resolve()/'voice-worklet.js'
    if not path.is_file():return JSONResponse(status_code=404,content={'detail':'语音资源未构建'})
    return FileResponse(path,media_type='application/javascript')

@app.api_route('/{path:path}', methods=['GET', 'HEAD'], include_in_schema=False)
def spa(path: str):
    if path == 'api' or path.startswith('api/'):
        return JSONResponse(status_code=404, content={'detail': '接口不存在'})
    if path == 'public' or path.startswith('public/'):
        return JSONResponse(status_code=404, content={'detail': '公开应用使用独立Application域，不在平台/public路径托管'})
    if (DIST / 'index.html').is_file():
        return FileResponse(DIST / 'index.html')
    return JSONResponse(status_code=503, content={'detail': '前端未构建；开发时请访问Vite服务'})
