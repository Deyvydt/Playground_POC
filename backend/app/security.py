import base64
import hashlib
import hmac
import json
import secrets
import time
from fastapi import Depends, HTTPException, Request
from sqlmodel import Session
from app.config import SECRET_KEY, TOKEN_TTL_HOURS
from app.database import get_session
from app.models import User

_PBKDF2_ROUNDS = 240_000

PERMISSIONS = {
    "admin": {"chat", "create", "edit", "delete", "knowledge", "metrics", "manage_users"},
    "developer": {"chat", "create", "edit", "knowledge", "metrics"},
    "viewer": {"chat"},
}


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _PBKDF2_ROUNDS).hex()
    return f"pbkdf2${_PBKDF2_ROUNDS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt, digest = stored.split("$")
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(rounds)).hex()
    return hmac.compare_digest(candidate, digest)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_token(user_id: int) -> str:
    payload = _b64(json.dumps({"sub": user_id, "exp": int(time.time()) + TOKEN_TTL_HOURS * 3600}).encode())
    signature = _b64(hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def _decode_token(token: str) -> int | None:
    try:
        payload, signature = token.split(".")
    except ValueError:
        return None
    expected = _b64(hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, signature):
        return None
    data = json.loads(_unb64(payload))
    if data.get("exp", 0) < time.time():
        return None
    return data.get("sub")


def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    header = request.headers.get("Authorization", "")
    token = header.removeprefix("Bearer ").strip()
    user_id = _decode_token(token) if token else None
    user = session.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        raise HTTPException(401, "Sesión no válida o expirada")
    return user


def require(permission: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if permission not in PERMISSIONS.get(user.role, set()):
            raise HTTPException(403, "No tienes permisos para realizar esta acción")
        return user

    return checker


def public_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "title": user.title,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "permissions": sorted(PERMISSIONS.get(user.role, set())),
    }
