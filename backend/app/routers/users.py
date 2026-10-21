from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.security import get_current_user, hash_password, public_user, require

router = APIRouter(prefix="/api/users", tags=["users"])


def _email_taken(session: Session, email: str, exclude_id: int | None = None) -> bool:
    found = session.exec(select(User).where(User.email == email)).first()
    return bool(found and found.id != exclude_id)


@router.get("")
def list_users(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    return [public_user(u) for u in session.exec(select(User).order_by(User.id)).all()]


@router.post("", status_code=201)
def create_user(payload: UserCreate, session: Session = Depends(get_session), _: User = Depends(require("manage_users"))):
    email = payload.email.strip().lower()
    if _email_taken(session, email):
        raise HTTPException(409, "Ya existe un usuario con ese correo")
    user = User(
        name=payload.name.strip(),
        email=email,
        title=payload.title.strip(),
        role=payload.role,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return public_user(user)


@router.put("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    actor: User = Depends(require("manage_users")),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    data = payload.model_dump(exclude_unset=True)
    if user.id == actor.id and (data.get("role", user.role) != "admin" or data.get("is_active") is False):
        raise HTTPException(400, "No puedes quitarte el rol de administrador ni desactivar tu propia cuenta")
    if "email" in data:
        data["email"] = data["email"].strip().lower()
        if _email_taken(session, data["email"], exclude_id=user.id):
            raise HTTPException(409, "Ya existe un usuario con ese correo")
    password = data.pop("password", None)
    if password:
        user.password_hash = hash_password(password)
    for key, value in data.items():
        setattr(user, key, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return public_user(user)


@router.delete("/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session), actor: User = Depends(require("manage_users"))):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    if user.id == actor.id:
        raise HTTPException(400, "No puedes eliminar tu propia cuenta")
    session.delete(user)
    session.commit()
    return {"ok": True}
