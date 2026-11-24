from uuid import UUID
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.auth import StrictInput
from app.db import get_db
from app.models import Message, Project, User, Workspace, now, uid
from app.security import advisory_lock, current_user

router = APIRouter(prefix='/projects', tags=['projects'])

class CreateProject(StrictInput):
    prompt: str = Field(min_length=1, max_length=4000)
    idempotency_key: UUID
    config_id: UUID | None = None
    config_version: int | None = None

class RenameProject(StrictInput):
    name: str = Field(min_length=1, max_length=60)

class CreateMessage(StrictInput):
    content: str = Field(min_length=1, max_length=4000)
    idempotency_key: UUID

    @field_validator('content')
    @classmethod
    def reject_empty(cls, value):
        if not value.strip():
            raise ValueError('消息不能为空')
        return value

def owned(db, project_id, user):
    project = db.scalar(select(Project).where(Project.id == str(project_id), Project.owner_id == user.id))
    if not project:
        raise HTTPException(404, '项目不存在或不可访问')
    return project

def project_view(p,db=None):
    from app.models import GenerationRun,Publication
    run=db.scalar(select(GenerationRun).where(GenerationRun.project_id==p.id).order_by(GenerationRun.created_at.desc()).limit(1)) if db else None
    publication=db.scalar(select(Publication).where(Publication.project_id==p.id)) if db else None
    return {'id': p.id, 'name': p.name, 'initial_prompt': p.initial_prompt, 'current_build_id': p.current_build_id,
            'created_at': p.created_at.astimezone(timezone.utc), 'updated_at': p.updated_at.astimezone(timezone.utc), 'generation_status': run.status if run else 'idle', 'publication_status': publication.status if publication else 'unpublished'}

def message_view(m):
    return {'id': m.id, 'role': m.role, 'content': m.content, 'created_at': m.created_at.astimezone(timezone.utc)}

@router.get('')
def list_projects(q: str = Query('', max_length=60), status:str=Query('all',pattern='^(all|preview|active|failed)$'), offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=20),
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    clause = [Project.owner_id == user.id]
    if q.strip():
        clause.append(Project.name.ilike('%' + q.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%', escape='\\'))
    from app.models import GenerationRun
    if status=='preview':clause.append(Project.current_build_id.is_not(None))
    elif status in ('active','failed'):
        last_status=select(GenerationRun.status).where(GenerationRun.project_id==Project.id).order_by(GenerationRun.created_at.desc()).limit(1).scalar_subquery()
        clause.append(last_status.in_(('queued','planning','generating','validating','cancelling')) if status=='active' else last_status.in_(('failed','interrupted','save_failed')))
    items = db.scalars(select(Project).where(*clause).order_by(Project.updated_at.desc(), Project.id).offset(offset).limit(limit)).all()
    total = db.scalar(select(func.count()).select_from(Project).where(*clause))
    return {'items': [project_view(p,db) for p in items], 'total': total, 'has_more': offset + len(items) < total}

@router.post('', status_code=201)
def create_project(body: CreateProject, user: User = Depends(current_user), db: Session = Depends(get_db)):
    key = str(body.idempotency_key)
    advisory_lock(db, 'project:' + user.id + ':' + key)
    existing = db.scalar(select(Project).where(Project.owner_id == user.id, Project.idempotency_key == key))
    if existing:
        if existing.initial_prompt != body.prompt:
            raise HTTPException(409, '幂等键已用于不同请求')
        return project_view(existing,db)
    from app.api.model_config import enabled_config
    advisory_lock(db,'model:'+user.id)
    config=enabled_config(db,user,body.config_id,body.config_version)
    workspace = db.scalar(select(Workspace).where(Workspace.owner_id == user.id))
    project = Project(id=uid(), owner_id=user.id, workspace_id=workspace.id, name=body.prompt.split('\n')[0][:40], initial_prompt=body.prompt, idempotency_key=key)
    db.add(project)
    db.flush()
    message=Message(id=uid(),project_id=project.id,idempotency_key=key,content=body.prompt)
    db.add(message);db.flush()
    from app.api.generation import enqueue
    enqueue(db,project,config,message,key)
    db.commit()
    return project_view(project,db)

@router.get('/{project_id}')
def get_project(project_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return project_view(owned(db, project_id, user),db)

@router.patch('/{project_id}')
def rename(project_id: UUID, body: RenameProject, user: User = Depends(current_user), db: Session = Depends(get_db)):
    project = owned(db, project_id, user)
    project.name, project.updated_at = body.name, now()
    db.commit()
    return project_view(project,db)

@router.get('/{project_id}/messages')
def messages(project_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned(db, project_id, user)
    items = db.scalars(select(Message).where(Message.project_id == str(project_id)).order_by(Message.created_at, Message.id).offset(offset).limit(limit)).all()
    return {'items': [message_view(m) for m in items]}

@router.post('/{project_id}/messages', status_code=201)
def add_message(project_id: UUID, body: CreateMessage, user: User = Depends(current_user), db: Session = Depends(get_db)):
    project = owned(db, project_id, user)
    from app.api.model_config import enabled_config
    enabled_config(db,user)
    key = str(body.idempotency_key)
    advisory_lock(db, 'message:' + project.id + ':' + key)
    previous = db.scalar(select(Message).where(Message.project_id == project.id, Message.idempotency_key == key))
    if previous:
        if previous.content != body.content:
            raise HTTPException(409, '幂等键已用于不同消息')
        return message_view(previous)
    message = Message(id=uid(), project_id=project.id, idempotency_key=key, content=body.content)
    db.add(message)
    project.updated_at = now()
    db.commit()
    return message_view(message)
