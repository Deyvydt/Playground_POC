from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.models import User

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()
