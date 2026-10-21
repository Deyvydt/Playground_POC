"""Validación real del token de sesión contra el servicio de identidad (transporte HTTP simulado)."""
import asyncio

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app import auth



def request_con(headers: dict) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "headers": raw, "method": "GET", "path": "/"})


@pytest.fixture
def identidad(monkeypatch):
    state = {"calls": 0, "responder": lambda req: httpx.Response(200, json={"name": "Ana Ríos", "role": "admin"})}
    real = httpx.AsyncClient

    def factory(*args, **kwargs):
        def handler(req):
            state["calls"] += 1
            return state["responder"](req)
        kwargs["transport"] = httpx.MockTransport(handler)
        return real(*args, **kwargs)

    monkeypatch.setattr(auth.httpx, "AsyncClient", factory)
    auth._cache.clear()
    return state


def test_el_token_de_servicio_identifica_al_servicio_que_llama(identidad):
    caller = asyncio.run(auth.get_caller(request_con({"X-Service-Token": "token-servicio-pruebas", "X-Service-Name": "agent-lab"})))
    assert (caller.name, caller.role, caller.is_admin) == ("agent-lab", "service", True)
    assert identidad["calls"] == 0


def test_la_sesion_de_tokenio_se_valida_contra_el_servicio_de_identidad_y_se_cachea(identidad):
    for _ in range(3):
        caller = asyncio.run(auth.get_caller(request_con({"Authorization": "Bearer abc"})))
    assert (caller.name, caller.role) == ("Ana Ríos", "admin")
    assert identidad["calls"] == 1


@pytest.mark.parametrize("headers", [{}, {"X-Service-Token": "incorrecto"}, {"X-Service-Token": "tókenñ"}])
def test_sin_credenciales_validas_responde_401(identidad, headers):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.get_caller(request_con(headers)))
    assert exc.value.status_code == 401


def test_sesion_rechazada_por_identidad_responde_401(identidad):
    identidad["responder"] = lambda req: httpx.Response(401)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.get_caller(request_con({"Authorization": "Bearer vencido"})))
    assert exc.value.status_code == 401


def test_identidad_caida_responde_503(identidad):
    def caido(req):
        raise httpx.ConnectError("sin conexión")
    identidad["responder"] = caido
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.get_caller(request_con({"Authorization": "Bearer abc"})))
    assert exc.value.status_code == 503


@pytest.mark.parametrize("role, permitido", [("admin", True), ("service", True), ("developer", False), ("viewer", False)])
def test_require_admin(role, permitido):
    caller = auth.Caller(name="x", role=role)
    if permitido:
        assert auth.require_admin(caller) is caller
    else:
        with pytest.raises(HTTPException) as exc:
            auth.require_admin(caller)
        assert exc.value.status_code == 403
