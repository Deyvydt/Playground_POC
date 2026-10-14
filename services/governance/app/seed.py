"""Organización, áreas y sistemas base. Idempotente."""
from sqlmodel import Session, select
from app.models import Area, Organization, Sistema

AREAS = [
    ("rrhh", "Recursos Humanos"),
    ("desarrollo", "Desarrollo"),
    ("plataforma", "Plataforma"),
]

SISTEMAS = [
    ("talentia", "Talentia", "rrhh", "Sistema de selección y gestión de talento."),
    ("agentfactory", "AgentFactory", "desarrollo", "Fábrica de software Java/Quarkus asistida por agentes."),
    ("tokenio", "TokenIO", "plataforma", "Agentes internos de la plataforma."),
]


def run_seed(session: Session) -> None:
    org = session.exec(select(Organization)).first()
    if not org:
        org = Organization(name="TCS")
        session.add(org)
        session.commit()
        session.refresh(org)
    for area_id, name in AREAS:
        if not session.get(Area, area_id):
            session.add(Area(id=area_id, name=name, organization_id=org.id))
    session.commit()
    for slug, name, area_id, description in SISTEMAS:
        if not session.exec(select(Sistema).where(Sistema.slug == slug)).first():
            session.add(Sistema(slug=slug, name=name, area_id=area_id, description=description))
    session.commit()
