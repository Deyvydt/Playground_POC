"""Autenticación delegada al servicio de identidad (backend de TokenIO).

Igual que en services/governance/app/auth.py: los usuarios envían el token de sesión
de TokenIO; agent-lab lo valida contra /api/auth/me. Los servicios internos usan
el header X-Service-Token.
"""
import secrets
import time
from dataclasses import dataclass
import httpx
from fastapi import Depends, HTTPException, Request
from app.config import IDENTITY_URL, SERVICE_TOKEN

_CACHE_SECONDS = 60
_cache: dict[str, tuple[float, "Caller"]] = {}


@dataclass
class Caller:
    name: str
    role: str  # admin | developer | viewer | service

    @property
    def is_admin(self) -> bool:
        return self.role in ("admin", "service")


async def get_caller(request: Request) -> Caller:
    service_token = request.headers.get("X-Service-Token", "")
    if service_token and secrets.compare_digest(service_token, SERVICE_TOKEN):
        return Caller(name=request.headers.get("X-Service-Name", "servicio"), role="service")

    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Sesión no válida o expirada")
    cached = _cache.get(token)
    if cached and cached[0] > time.time():
        return cached[1]
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            r = await client.get(f"{IDENTITY_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    except httpx.HTTPError as exc:
        raise HTTPException(503, "El servicio de identidad no está disponible") from exc
    if r.status_code != 200:
        raise HTTPException(401, "Sesión no válida o expirada")
    user = r.json()
    caller = Caller(name=user.get("name", ""), role=user.get("role", "viewer"))
    _cache[token] = (time.time() + _CACHE_SECONDS, caller)
    return caller


def require_admin(caller: Caller = Depends(get_caller)) -> Caller:
    if not caller.is_admin:
        raise HTTPException(403, "No tienes permisos para realizar esta acción")
    return caller
