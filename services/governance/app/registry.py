"""Reglas de negocio del registro de agentes: alta, kill switch, regeneración de key y consumo."""
import asyncio
import re
import unicodedata
from datetime import datetime
from sqlmodel import Session, select
from app import litellm_admin
from app.config import GATEWAY_PUBLIC_URL
from app.models import Agente, Notification, Sistema
from app.notify import notify

AUTO = "automático"


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "agente"


def _key_fields(agente: Agente, sistema: Sistema) -> dict:
    return {
        "key_alias": agente.key_alias,
        "team_id": agente.area_id,
        "models": agente.models,
        "max_budget": agente.max_budget,
        "budget_duration": agente.budget_duration,
        "tpm_limit": agente.tpm_limit,
        "rpm_limit": agente.rpm_limit,
        "metadata": {"agent_id": agente.id, "agent_name": agente.name, "sistema": sistema.slug, "area": agente.area_id},
    }


async def _issue_key(session: Session, agente: Agente) -> str:
    sistema = session.get(Sistema, agente.sistema_id)
    data = await litellm_admin.generate_key(**_key_fields(agente, sistema))
    agente.key_hash = data["token"]
    return data["key"]


async def register(session: Session, agente: Agente, registered_by: str) -> str:
    """Crea el agente y su virtual key. Devuelve la key en claro (única vez que existe fuera del gateway)."""
    sistema = session.get(Sistema, agente.sistema_id)
    agente.area_id = sistema.area_id
    agente.slug = slugify(agente.name)
    agente.key_alias = f"{sistema.slug}/{agente.slug}"
    if session.exec(select(Agente).where(Agente.key_alias == agente.key_alias)).first():
        raise ValueError(f"Ya existe un agente '{agente.name}' en {sistema.name}")
    agente.key_hash = "pendiente"
    session.add(agente)
    session.commit()
    session.refresh(agente)
    try:
        key = await _issue_key(session, agente)
    except litellm_admin.GatewayError:
        # Sin key el registro no sirve: se revierte para no dejar agentes huérfanos.
        session.delete(agente)
        session.commit()
        raise
    session.add(agente)
    session.commit()
    session.refresh(agente)
    notify(session, "registro", f"Agente registrado: {agente.name}", f"{sistema.name} · registrado por {registered_by}", agente=agente)
    return key


async def regenerate_key(session: Session, agente: Agente, by: str) -> str:
    old_hash = agente.key_hash
    await litellm_admin.delete_key(old_hash)
    key = await _issue_key(session, agente)
    if agente.status == "pausado":
        await litellm_admin.block_key(agente.key_hash)
    agente.updated_at = datetime.utcnow()
    session.add(agente)
    session.commit()
    notify(session, "regeneracion", f"Key regenerada: {agente.name}", f"La key anterior quedó invalidada · {by}", agente=agente)
    return key


async def update_limits(session: Session, agente: Agente, changes: dict) -> Agente:
    for field, value in changes.items():
        setattr(agente, field, value)
    sistema = session.get(Sistema, agente.sistema_id)
    fields = _key_fields(agente, sistema)
    fields.pop("key_alias")
    await litellm_admin.update_key(agente.key_hash, **fields)
    agente.budget_warning_sent = False
    agente.updated_at = datetime.utcnow()
    session.add(agente)
    session.commit()
    session.refresh(agente)
    return agente


async def pause(session: Session, agente: Agente, reason: str, by: str, kind: str = "pausa_manual") -> Agente:
    if agente.status == "pausado":
        return agente
    await litellm_admin.block_key(agente.key_hash)
    agente.status = "pausado"
    agente.pause_reason = reason
    agente.paused_by = by
    agente.paused_at = datetime.utcnow()
    session.add(agente)
    session.commit()
    session.refresh(agente)
    severity = "warning" if kind == "pausa_manual" else "critical"
    title = f"Agente pausado: {agente.name}" if kind == "pausa_manual" else f"Pausa automática: {agente.name}"
    notify(session, kind, title, f"{reason} · {by}", severity=severity, agente=agente)
    return agente


async def resume(session: Session, agente: Agente, by: str) -> Agente:
    if agente.status == "activo":
        return agente
    await litellm_admin.unblock_key(agente.key_hash)
    agente.status = "activo"
    agente.pause_reason = None
    agente.paused_by = None
    agente.paused_at = None
    agente.budget_warning_sent = False
    session.add(agente)
    session.commit()
    session.refresh(agente)
    notify(session, "reactivacion", f"Agente reactivado: {agente.name}", f"Reactivado por {by}", agente=agente)
    return agente


async def deregister(session: Session, agente: Agente, by: str) -> None:
    await litellm_admin.delete_key(agente.key_hash)
    for n in session.exec(select(Notification).where(Notification.agente_id == agente.id)).all():
        n.agente_id = None
        session.add(n)
    name, area_id = agente.name, agente.area_id
    session.delete(agente)
    session.commit()
    notify(session, "baja", f"Agente dado de baja: {name}", f"Su key fue eliminada · {by}", area_id=area_id)


async def usage(agente: Agente) -> dict:
    try:
        info = await litellm_admin.key_info(agente.key_hash)
    except litellm_admin.GatewayError:
        return {"available": False}
    spend = float(info.get("spend") or 0)
    budget = info.get("max_budget")
    return {
        "available": True,
        "spend": spend,
        "max_budget": budget,
        "budget_ratio": (spend / budget) if budget else None,
        "budget_reset_at": info.get("budget_reset_at"),
        "blocked": bool(info.get("blocked")),
        "last_active": info.get("last_active"),
    }


async def usage_many(agentes: list[Agente]) -> dict[int, dict]:
    results = await asyncio.gather(*(usage(a) for a in agentes))
    return {a.id: u for a, u in zip(agentes, results)}


def connection_guide(agente: Agente, key: str) -> dict:
    base_url = f"{GATEWAY_PUBLIC_URL}/v1"
    model = "llama-local"
    return {
        "base_url": base_url,
        "api_key": key,
        "models": agente.models,
        "example_model": model,
        "python": (
            "from langchain_openai import ChatOpenAI\n\n"
            f'llm = ChatOpenAI(base_url="{base_url}", api_key="<VIRTUAL_KEY>", model="{model}")\n'
            'print(llm.invoke("Hola").content)\n'
        ),
        "java": (
            "// Quarkus + LangChain4j (application.properties)\n"
            f"quarkus.langchain4j.openai.base-url={base_url}\n"
            "quarkus.langchain4j.openai.api-key=${VIRTUAL_KEY}\n"
            f"quarkus.langchain4j.openai.chat-model.model-name={model}\n"
        ),
        "curl": (
            f"curl {base_url}/chat/completions \\\n"
            '  -H "Authorization: Bearer <VIRTUAL_KEY>" -H "Content-Type: application/json" \\\n'
            f"  -d '{{\"model\": \"{model}\", \"messages\": [{{\"role\": \"user\", \"content\": \"Hola\"}}]}}'\n"
        ),
    }
