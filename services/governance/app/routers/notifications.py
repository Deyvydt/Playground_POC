from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select, update
from app.auth import Caller, get_caller
from app.database import get_session
from app.models import Notification

router = APIRouter(prefix="/gov/notifications", tags=["notifications"])


@router.get("")
def list_notifications(
    unread_only: bool = False,
    # ge=1: Postgres rechaza un LIMIT negativo (500); por arriba se recorta a 200.
    limit: int = Query(50, ge=1),
    session: Session = Depends(get_session),
    _: Caller = Depends(get_caller),
):
    query = select(Notification).order_by(Notification.created_at.desc()).limit(min(limit, 200))
    if unread_only:
        query = query.where(Notification.read == False)  # noqa: E712
    unread = session.exec(select(func.count()).select_from(Notification).where(Notification.read == False)).one()  # noqa: E712
    return {"unread": unread, "items": session.exec(query).all()}


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, session: Session = Depends(get_session), _: Caller = Depends(get_caller)):
    n = session.get(Notification, notification_id)
    if not n:
        raise HTTPException(404, "Notificación no encontrada")
    n.read = True
    session.add(n)
    session.commit()
    return {"ok": True}


@router.post("/read-all")
def mark_all_read(session: Session = Depends(get_session), _: Caller = Depends(get_caller)):
    session.exec(update(Notification).where(Notification.read == False).values(read=True))  # noqa: E712
    session.commit()
    return {"ok": True}
