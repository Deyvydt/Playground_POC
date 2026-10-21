"""Utilidades compartidas por las pruebas de governance."""
from sqlmodel import Session, select

from app.database import engine
from app.models import Agente, Notification, Sistema


def sistema_id(slug: str) -> int:
    with Session(engine) as session:
        return session.exec(select(Sistema).where(Sistema.slug == slug)).one().id


def agente(agent_id: int) -> Agente:
    with Session(engine) as session:
        return session.get(Agente, agent_id)


def avisos(kind: str | None = None) -> list[Notification]:
    with Session(engine) as session:
        query = select(Notification)
        if kind:
            query = query.where(Notification.kind == kind)
        return session.exec(query).all()


def registrar(client, headers, nombre="Agente de Prueba", sistema="agentfactory", **extra):
    payload = {"name": nombre, "sistema_id": sistema_id(sistema), **extra}
    return client.post("/gov/agents", json=payload, headers=headers)
