"""Único punto de contacto de governance con la API de administración del gateway."""
from datetime import datetime, timedelta
import httpx
from app.config import GATEWAY_URL, LITELLM_MASTER_KEY

TIMEOUT = httpx.Timeout(30.0, connect=5.0)


class GatewayError(RuntimeError):
    """El gateway no respondió o rechazó la operación."""


async def _request(method: str, path: str, **kwargs) -> dict | list:
    try:
        async with httpx.AsyncClient(
            base_url=GATEWAY_URL, timeout=TIMEOUT, headers={"Authorization": f"Bearer {LITELLM_MASTER_KEY}"}
        ) as client:
            r = await client.request(method, path, **kwargs)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as exc:
        raise GatewayError(f"El gateway rechazó la operación ({exc.response.status_code}): {exc.response.text[:200]}") from exc
    except httpx.HTTPError as exc:
        raise GatewayError("El gateway no está disponible") from exc


async def is_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
            return (await client.get(f"{GATEWAY_URL}/health/liveliness")).status_code == 200
    except httpx.HTTPError:
        return False


async def generate_key(**fields) -> dict:
    return await _request("POST", "/key/generate", json=fields)


async def update_key(key_hash: str, **fields) -> dict:
    return await _request("POST", "/key/update", json={"key": key_hash, **fields})


async def delete_key(key_hash: str) -> None:
    await _request("POST", "/key/delete", json={"keys": [key_hash]})


async def block_key(key_hash: str) -> None:
    await _request("POST", "/key/block", json={"key": key_hash})


async def unblock_key(key_hash: str) -> None:
    await _request("POST", "/key/unblock", json={"key": key_hash})


async def key_info(key_hash: str) -> dict:
    data = await _request("GET", "/key/info", params={"key": key_hash})
    return data.get("info", {})


async def team_info(team_id: str) -> dict:
    data = await _request("GET", "/team/info", params={"team_id": team_id})
    return data.get("team_info", {})


async def recent_logs(key_hash: str, minutes: int) -> list[dict]:
    """Registros de llamadas de la key en los últimos `minutes` minutos (incluye las fallidas)."""
    since = datetime.utcnow() - timedelta(minutes=minutes)
    data = await _request("GET", "/spend/logs", params={"api_key": key_hash})
    logs = data if isinstance(data, list) else []
    return [log for log in logs if _parse(log.get("startTime")) >= since]


def _parse(value: str | None) -> datetime:
    if not value:
        return datetime.min
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
