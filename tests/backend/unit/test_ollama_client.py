"""Camino por gateway de ollama_client con un transporte HTTP simulado (sin red)."""
import asyncio
import json

import httpx
import pytest

from app import ollama_client
from support import ORIGINALS


@pytest.fixture
def gateway(monkeypatch):
    """Activa el modo gateway y captura las solicitudes; `responder` define la respuesta."""
    state = {"requests": [], "responder": lambda req: httpx.Response(200, json=CHAT_OK)}
    real_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(lambda req: state["requests"].append(req) or state["responder"](req))
        return real_client(*args, **kwargs)

    monkeypatch.setattr(ollama_client.httpx, "AsyncClient", client_factory)
    monkeypatch.setattr(ollama_client, "LLM_GATEWAY_URL", "http://gateway.test")
    return state


CHAT_OK = {
    "choices": [{"message": {"role": "assistant", "content": "Hola desde el gateway"}}],
    "usage": {"prompt_tokens": 12, "completion_tokens": 3},
}


def test_chat_por_gateway_envia_key_metadata_y_traduce_al_formato_de_ollama(gateway):
    result = asyncio.run(ORIGINALS["chat"]("llama-local", [{"role": "user", "content": "Hola"}],
                                           api_key="sk-agente", metadata={"trace_id": "t-1"}))
    request = gateway["requests"][0]
    body = json.loads(request.content)
    assert request.url == "http://gateway.test/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer sk-agente"
    assert body["metadata"] == {"trace_id": "t-1"} and body["model"] == "llama-local"
    assert result == {"message": {"role": "assistant", "content": "Hola desde el gateway"},
                      "prompt_eval_count": 12, "eval_count": 3}


def test_chat_por_gateway_sin_metadata_no_envia_el_campo(gateway):
    asyncio.run(ORIGINALS["chat"]("llama-local", [{"role": "user", "content": "Hola"}], api_key="sk"))
    assert "metadata" not in json.loads(gateway["requests"][0].content)


@pytest.mark.particion
@pytest.mark.parametrize("status, mensaje", [
    (401, "El agente está pausado por un administrador."),
    (400, "El agente agotó su presupuesto o límite de uso."),
    (422, "El agente agotó su presupuesto o límite de uso."),
    (429, "El agente agotó su presupuesto o límite de uso."),
    (500, "El gateway rechazó la solicitud (500)."),
])
def test_errores_del_gateway_se_traducen_a_mensajes_claros(gateway, status, mensaje):
    gateway["responder"] = lambda req: httpx.Response(status, json={"error": "x"})
    with pytest.raises(ollama_client.ModelUnavailableError, match=mensaje.replace("(", r"\(").replace(")", r"\)").replace(".", r"\.")):
        asyncio.run(ORIGINALS["chat"]("llama-local", [{"role": "user", "content": "Hola"}], api_key="sk"))


@pytest.mark.adivinanza_errores
def test_gateway_caido_se_informa_como_no_disponible(gateway):
    def caido(req):
        raise httpx.ConnectError("sin conexión")
    gateway["responder"] = caido
    with pytest.raises(ollama_client.ModelUnavailableError, match="no está disponible"):
        asyncio.run(ORIGINALS["chat"]("llama-local", [{"role": "user", "content": "Hola"}], api_key="sk"))


def test_embeddings_por_gateway_usan_el_alias_y_la_key_del_agente(gateway):
    gateway["responder"] = lambda req: httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2]}]})
    vector = asyncio.run(ORIGINALS["embed"]("texto", api_key="sk-agente", metadata={"trace_id": "t"}))
    body = json.loads(gateway["requests"][0].content)
    assert vector == [0.1, 0.2]
    assert body == {"model": "embed-local", "input": "texto", "metadata": {"trace_id": "t"}}
