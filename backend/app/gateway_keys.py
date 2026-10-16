"""Alta de los agentes de TokenIO como clientes del gateway (virtual keys).

Solo actua si LLM_GATEWAY_URL esta configurado. Cada agente se registra una vez en
governance (sistema "tokenio", area "plataforma") y su virtual key queda cifrada
(Fernet) en Agent.gateway_key_enc; la key en claro nunca se guarda.
"""
import logging
import httpx
from cryptography.fernet import Fernet
from sqlmodel import Session, select
from app.config import GATEWAY_FERNET_KEY, GOVERNANCE_URL, LLM_GATEWAY_URL, SERVICE_TOKEN
from app.models import Agent
from app.ollama_client import ModelUnavailableError

logger = logging.getLogger("gateway_keys")

HEADERS = {"X-Service-Token": SERVICE_TOKEN, "X-Service-Name": "tokenio-backend"}


def _fernet() -> Fernet:
    return Fernet(GATEWAY_FERNET_KEY.encode())


def encrypt(key: str) -> str:
    return _fernet().encrypt(key.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


def api_key_for(agent: Agent) -> str | None:
    """Key en claro del agente para llamar al gateway, o None si el camino directo esta activo."""
    if not LLM_GATEWAY_URL:
        return None
    if not agent.gateway_key_enc:
        raise ModelUnavailableError(
            "El agente todavía no está registrado en el gateway. Espera unos segundos o reinicia el backend."
        )
    return decrypt(agent.gateway_key_enc)


async def register_missing(session: Session) -> None:
    """Registra en governance los agentes de TokenIO sin virtual key. Idempotente."""
    if not LLM_GATEWAY_URL:
        return
    pending = session.exec(select(Agent).where(Agent.gateway_key_enc.is_(None))).all()
    if not pending:
        return
    try:
        async with httpx.AsyncClient(base_url=GOVERNANCE_URL, headers=HEADERS, timeout=30) as client:
            r = await client.get("/gov/sistemas")
            r.raise_for_status()
            sistema_id = next((s["id"] for s in r.json() if s["slug"] == "tokenio"), None)
            if sistema_id is None:
                logger.warning("Sistema 'tokenio' no existe en governance; no se pueden registrar agentes.")
                return
            for agent in pending:
                payload = {
                    "name": agent.name,
                    "sistema_id": sistema_id,
                    "description": agent.description,
                    "runtime": "external",
                    "models": ["local-models"],
                }
                r = await client.post("/gov/agents", json=payload)
                r.raise_for_status()
                agent.gateway_key_enc = encrypt(r.json()["connection"]["api_key"])
                session.add(agent)
                session.commit()
                logger.info("Agente '%s' registrado en el gateway.", agent.name)
    except httpx.HTTPError as exc:
        logger.warning("No se pudieron registrar todos los agentes en el gateway: %s", exc)
