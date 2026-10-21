"""Revisión periódica de agentes activos: avisos y auto-pausa por gasto o tasa de errores."""
import asyncio
import logging
from sqlmodel import Session, select
from app import litellm_admin, registry
from app.config import (
    BUDGET_WARNING_RATIO,
    ERROR_MIN_CALLS,
    ERROR_RATE_THRESHOLD,
    ERROR_WINDOW_MINUTES,
    MONITOR_INTERVAL_SECONDS,
)
from app.database import engine
from app.models import Agente
from app.notify import notify

log = logging.getLogger("governance.monitor")


async def check_agent(session: Session, agente: Agente) -> None:
    usage = await registry.usage(agente)
    if not usage["available"]:
        return
    ratio = usage["budget_ratio"]
    if ratio is not None and ratio >= 1:
        await registry.pause(
            session, agente,
            f"Superó su presupuesto (${usage['spend']:.4f} de ${usage['max_budget']:.4f})",
            registry.AUTO, kind="auto_pausa_gasto",
        )
        return
    if ratio is not None and ratio >= BUDGET_WARNING_RATIO and not agente.budget_warning_sent:
        agente.budget_warning_sent = True
        session.add(agente)
        session.commit()
        notify(
            session, "aviso_gasto", f"Gasto alto: {agente.name}",
            f"Consumió el {ratio:.0%} de su presupuesto (${usage['spend']:.4f} de ${usage['max_budget']:.4f})",
            severity="warning", agente=agente,
        )

    logs = await litellm_admin.recent_logs(agente.key_hash, ERROR_WINDOW_MINUTES)
    if len(logs) >= ERROR_MIN_CALLS:
        failures = sum(1 for entry in logs if entry.get("status") == "failure")
        rate = failures / len(logs)
        if rate > ERROR_RATE_THRESHOLD:
            await registry.pause(
                session, agente,
                f"Tasa de errores de {rate:.0%} ({failures} de {len(logs)} llamadas en {ERROR_WINDOW_MINUTES} min)",
                registry.AUTO, kind="auto_pausa_errores",
            )


async def run_once() -> None:
    with Session(engine) as session:
        for agente in session.exec(select(Agente).where(Agente.status == "activo")).all():
            try:
                await check_agent(session, agente)
            except litellm_admin.GatewayError as exc:
                log.warning("No se pudo revisar el agente %s: %s", agente.key_alias, exc)


async def loop() -> None:
    while True:
        await asyncio.sleep(MONITOR_INTERVAL_SECONDS)
        try:
            await run_once()
        except Exception:
            log.exception("Fallo en el ciclo del monitor")
