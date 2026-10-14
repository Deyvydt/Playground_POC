"""Recibe las alertas de presupuesto que el gateway envía por webhook."""
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from app import litellm_admin, registry
from app.config import WEBHOOK_TOKEN
from app.database import get_session
from app.models import Agente
from app.notify import notify

router = APIRouter(prefix="/gov/alerts", tags=["alerts"])


@router.post("/gateway")
async def gateway_alert(request: Request, token: str = "", session: Session = Depends(get_session)):
    # El webhook del gateway no admite headers propios; el secreto viaja en la URL.
    if not secrets.compare_digest(token, WEBHOOK_TOKEN):
        raise HTTPException(401, "Token inválido")
    payload = await request.json()
    event = payload.get("event", "")
    message = payload.get("event_message") or event
    agente = None
    if payload.get("token"):
        agente = session.exec(select(Agente).where(Agente.key_hash == payload["token"])).first()

    if agente and event == "budget_crossed":
        try:
            await registry.pause(session, agente, "El gateway reportó presupuesto superado", registry.AUTO, kind="auto_pausa_gasto")
        except litellm_admin.GatewayError:
            pass  # el monitor lo reintentará
    else:
        severity = "critical" if event == "budget_crossed" else "warning"
        notify(
            session, "alerta_gateway", message,
            f"Gasto ${float(payload.get('spend') or 0):.4f} de ${float(payload.get('max_budget') or 0):.4f}",
            severity=severity, agente=agente, area_id=payload.get("team_id"),
        )
    return {"ok": True}
