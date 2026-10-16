"""Almacén cifrado de las virtual keys de los nodos (Fernet; clave en LAB_FERNET_KEY)."""
from cryptography.fernet import Fernet
from sqlmodel import Session, select
from app.config import LAB_FERNET_KEY
from app.database import engine
from app.models import AgentCredential

_fernet = Fernet(LAB_FERNET_KEY.encode())


def _encrypt(key: str) -> str:
    return _fernet.encrypt(key.encode()).decode()


def _decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()


def _find(session: Session, sistema: str, nodo: str) -> AgentCredential | None:
    return session.exec(
        select(AgentCredential).where(AgentCredential.sistema == sistema, AgentCredential.nodo == nodo)
    ).first()


def exists(sistema: str, nodo: str) -> bool:
    with Session(engine) as session:
        return _find(session, sistema, nodo) is not None


def save(sistema: str, nodo: str, agente_id: int, key_alias: str, key: str) -> None:
    with Session(engine) as session:
        cred = _find(session, sistema, nodo) or AgentCredential(
            sistema=sistema, nodo=nodo, agente_id=agente_id, key_alias=key_alias, key_enc=""
        )
        cred.agente_id = agente_id
        cred.key_alias = key_alias
        cred.key_enc = _encrypt(key)
        session.add(cred)
        session.commit()


def get_credential(sistema: str, nodo: str) -> tuple[int, str]:
    """Devuelve (agente_id, key en claro) del nodo. Falla si no se corrió provision.py."""
    with Session(engine) as session:
        cred = _find(session, sistema, nodo)
        if cred is None:
            raise RuntimeError(f"No hay credencial para {sistema}/{nodo}. Ejecuta provision.py primero.")
        return cred.agente_id, _decrypt(cred.key_enc)
