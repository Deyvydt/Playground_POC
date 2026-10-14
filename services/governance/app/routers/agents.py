from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app import litellm_admin, registry
from app.auth import Caller, get_caller, require_admin
from app.database import get_session
from app.models import Agente, Area, Notification, Sistema
from app.schemas import AgentIn, AgentLimitsIn, PauseIn

router = APIRouter(prefix="/gov/agents", tags=["agents"])


def _serialize(agente: Agente, session: Session, usage: dict | None = None) -> dict:
    sistema = session.get(Sistema, agente.sistema_id)
    area = session.get(Area, agente.area_id)
    data = agente.model_dump(exclude={"key_hash", "budget_warning_sent"})
    data["sistema"] = {"id": sistema.id, "slug": sistema.slug, "name": sistema.name}
    data["area"] = {"id": area.id, "name": area.name}
    if usage is not None:
        data["usage"] = usage
    return data


def _get(session: Session, agent_id: int) -> Agente:
    agente = session.get(Agente, agent_id)
    if not agente:
        raise HTTPException(404, "Agente no encontrado")
    return agente


def _gateway_error(exc: litellm_admin.GatewayError) -> HTTPException:
    return HTTPException(503, str(exc))


@router.get("")
async def list_agents(
    area_id: str | None = None,
    sistema_id: int | None = None,
    session: Session = Depends(get_session),
    _: Caller = Depends(get_caller),
):
    query = select(Agente).order_by(Agente.area_id, Agente.sistema_id, Agente.name)
    if area_id:
        query = query.where(Agente.area_id == area_id)
    if sistema_id:
        query = query.where(Agente.sistema_id == sistema_id)
    agentes = session.exec(query).all()
    usages = await registry.usage_many(agentes)
    return [_serialize(a, session, usages[a.id]) for a in agentes]


@router.post("", status_code=201)
async def register_agent(payload: AgentIn, session: Session = Depends(get_session), caller: Caller = Depends(require_admin)):
    if not session.get(Sistema, payload.sistema_id):
        raise HTTPException(404, "Sistema no encontrado")
    agente = Agente(**payload.model_dump(), area_id="", slug="", key_alias="", key_hash="")
    try:
        key = await registry.register(session, agente, caller.name)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    except litellm_admin.GatewayError as exc:
        raise _gateway_error(exc) from exc
    return {"agent": _serialize(agente, session), "connection": registry.connection_guide(agente, key)}


@router.get("/{agent_id}")
async def get_agent(agent_id: int, session: Session = Depends(get_session), _: Caller = Depends(get_caller)):
    agente = _get(session, agent_id)
    data = _serialize(agente, session, await registry.usage(agente))
    data["notifications"] = [
        n.model_dump()
        for n in session.exec(
            select(Notification).where(Notification.agente_id == agent_id).order_by(Notification.created_at.desc()).limit(20)
        ).all()
    ]
    return data


@router.get("/{agent_id}/activity")
async def agent_activity(agent_id: int, minutes: int = 1440, session: Session = Depends(get_session), _: Caller = Depends(get_caller)):
    agente = _get(session, agent_id)
    try:
        logs = await litellm_admin.recent_logs(agente.key_hash, minutes)
    except litellm_admin.GatewayError as exc:
        raise _gateway_error(exc) from exc
    return [
        {
            "at": log.get("startTime"),
            "model": log.get("model_group") or log.get("model"),
            "status": log.get("status"),
            "prompt_tokens": log.get("prompt_tokens", 0),
            "completion_tokens": log.get("completion_tokens", 0),
            "spend": log.get("spend", 0),
            "latency_ms": _latency_ms(log),
        }
        for log in logs
    ]


def _latency_ms(log: dict) -> int | None:
    start, end = log.get("startTime"), log.get("endTime")
    if not start or not end:
        return None
    return int((litellm_admin._parse(end) - litellm_admin._parse(start)).total_seconds() * 1000)


@router.patch("/{agent_id}")
async def update_agent(agent_id: int, payload: AgentLimitsIn, session: Session = Depends(get_session), _: Caller = Depends(require_admin)):
    agente = _get(session, agent_id)
    try:
        agente = await registry.update_limits(session, agente, payload.model_dump(exclude_unset=True))
    except litellm_admin.GatewayError as exc:
        raise _gateway_error(exc) from exc
    return _serialize(agente, session, await registry.usage(agente))


@router.post("/{agent_id}/pause")
async def pause_agent(agent_id: int, payload: PauseIn, session: Session = Depends(get_session), caller: Caller = Depends(require_admin)):
    try:
        agente = await registry.pause(session, _get(session, agent_id), payload.reason, caller.name)
    except litellm_admin.GatewayError as exc:
        raise _gateway_error(exc) from exc
    return _serialize(agente, session)


@router.post("/{agent_id}/resume")
async def resume_agent(agent_id: int, session: Session = Depends(get_session), caller: Caller = Depends(require_admin)):
    try:
        agente = await registry.resume(session, _get(session, agent_id), caller.name)
        usage = await registry.usage(agente)
    except litellm_admin.GatewayError as exc:
        raise _gateway_error(exc) from exc
    data = _serialize(agente, session, usage)
    if usage.get("budget_ratio") is not None and usage["budget_ratio"] >= 1:
        data["warning"] = "El agente sigue sin presupuesto disponible: el gateway rechazará sus llamadas hasta ampliarlo."
    return data


@router.delete("/{agent_id}", status_code=204)
async def deregister_agent(agent_id: int, session: Session = Depends(get_session), caller: Caller = Depends(require_admin)):
    try:
        await registry.deregister(session, _get(session, agent_id), caller.name)
    except litellm_admin.GatewayError as exc:
        raise _gateway_error(exc) from exc


@router.post("/{agent_id}/regenerate-key")
async def regenerate_key(agent_id: int, session: Session = Depends(get_session), caller: Caller = Depends(require_admin)):
    agente = _get(session, agent_id)
    try:
        key = await registry.regenerate_key(session, agente, caller.name)
    except litellm_admin.GatewayError as exc:
        raise _gateway_error(exc) from exc
    return {"agent": _serialize(agente, session), "connection": registry.connection_guide(agente, key)}
