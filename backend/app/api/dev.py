"""Only user-approved local mock; never configured in production."""
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.auth import StrictInput, issue_session
from app.config import settings
from app.db import get_db
from app.models import User, Workspace, uid
from app.security import advisory_lock

router=APIRouter(prefix='/dev',tags=['development mock'])
class MockLogin(StrictInput):
    account: str = Field(pattern=r'^(alice|bob)$')

@router.post('/mock-login')
def login(body:MockLogin,response:Response,db:Session=Depends(get_db)):
    if settings.production or not settings.dev_mock_auth:
        raise HTTPException(404,'开发Mock不可用')
    email=f'{body.account}@mock.invalid'
    advisory_lock(db,'user:'+email)
    user=db.scalar(select(User).where(User.email==email))
    if not user:
        user=User(id=uid(),email=email);db.add(user);db.flush();db.add(Workspace(owner_id=user.id))
    csrf=issue_session(db,user,response)
    from app.models import AuthSession
    db.flush()
    for session in db.scalars(select(AuthSession).where(AuthSession.user_id==user.id)):
        session.mock=True
    db.commit()
    return {'user':{'id':user.id,'email':user.email},'csrf_token':csrf,'mock':True}
