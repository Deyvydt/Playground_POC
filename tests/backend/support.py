"""Utilidades compartidas por las pruebas del backend (importar después de conftest)."""
from sqlmodel import Session, select

from app import ollama_client, security
from app.database import engine
from app.models import Agent, User

ROLE_EMAILS = {
    "admin": "ana.rios@tcs.com",
    "developer": "carlos.vega@tcs.com",
    "viewer": "lucia.soto@tcs.com",
    "administrador": "ana.rios@tcs.com",
    "desarrollador": "carlos.vega@tcs.com",
    "solo lectura": "lucia.soto@tcs.com",
}

# Funciones reales del cliente de modelos, antes de reemplazarlas por el doble.
ORIGINALS = {name: getattr(ollama_client, name) for name in ("chat", "embed", "is_available", "list_models")}


def user_by_email(email: str) -> User:
    with Session(engine) as session:
        return session.exec(select(User).where(User.email == email)).one()


def agent_by_name(name: str) -> Agent:
    with Session(engine) as session:
        return session.exec(select(Agent).where(Agent.name == name)).one()


def auth_headers(role_or_email: str) -> dict:
    email = ROLE_EMAILS.get(role_or_email, role_or_email)
    return {"Authorization": f"Bearer {security.create_token(user_by_email(email).id)}"}
