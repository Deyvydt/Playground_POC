from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.schemas import LoginRequest
from app.security import create_token, get_current_user, public_user, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email.strip().lower())).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Correo o contraseña incorrectos")
    if not user.is_active:
        raise HTTPException(403, "Tu cuenta está desactivada. Contacta a un administrador.")
    user.last_login_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"token": create_token(user.id), "user": public_user(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return public_user(user)
