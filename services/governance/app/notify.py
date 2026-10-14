from sqlmodel import Session
from app.models import Agente, Notification


def notify(
    session: Session,
    kind: str,
    title: str,
    message: str = "",
    severity: str = "info",
    agente: Agente | None = None,
    area_id: str | None = None,
) -> Notification:
    n = Notification(
        kind=kind,
        severity=severity,
        title=title,
        message=message,
        agente_id=agente.id if agente else None,
        area_id=agente.area_id if agente else area_id,
    )
    session.add(n)
    session.commit()
    session.refresh(n)
    return n
