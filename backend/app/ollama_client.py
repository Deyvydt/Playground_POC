import httpx
from app.config import EMBED_MODEL, LLM_GATEWAY_URL, OLLAMA_HOST

TIMEOUT = httpx.Timeout(120.0, connect=10.0)
GATEWAY_EMBED_ALIAS = "embed-local"


class ModelUnavailableError(RuntimeError):
    """El motor de modelos no respondio o rechazo la solicitud."""


def _gateway_error_message(exc: httpx.HTTPStatusError) -> str:
    status = exc.response.status_code
    if status == 401:
        return "El agente está pausado por un administrador."
    if status in (400, 422, 429):
        return "El agente agotó su presupuesto o límite de uso."
    return f"El gateway rechazó la solicitud ({status})."


async def list_models() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            r.raise_for_status()
            data = r.json()
            return data.get("models", [])
    except httpx.HTTPError:
        return []


async def list_models_gateway(api_key: str) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            r = await client.get(f"{LLM_GATEWAY_URL}/v1/models", headers={"Authorization": f"Bearer {api_key}"})
            r.raise_for_status()
            return r.json().get("data", [])
    except httpx.HTTPError:
        return []


async def is_available() -> bool:
    url = f"{LLM_GATEWAY_URL}/health/liveliness" if LLM_GATEWAY_URL else f"{OLLAMA_HOST}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
            r = await client.get(url)
            return r.status_code == 200
    except httpx.HTTPError:
        return False


async def chat(
    model: str,
    messages: list[dict],
    temperature: float = 0.4,
    tools: list[dict] | None = None,
    api_key: str | None = None,
) -> dict:
    if LLM_GATEWAY_URL:
        return await _chat_gateway(model, messages, temperature, tools, api_key)

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if tools:
        payload["tools"] = tools

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as exc:
        raise ModelUnavailableError(f"El modelo '{model}' respondió con error {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise ModelUnavailableError("El motor de modelos no está disponible") from exc


async def _chat_gateway(
    model: str, messages: list[dict], temperature: float, tools: list[dict] | None, api_key: str | None
) -> dict:
    payload = {"model": model, "messages": messages, "temperature": temperature}
    if tools:
        payload["tools"] = tools
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                f"{LLM_GATEWAY_URL}/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as exc:
        raise ModelUnavailableError(_gateway_error_message(exc)) from exc
    except httpx.HTTPError as exc:
        raise ModelUnavailableError("El gateway no está disponible") from exc
    choice = (data.get("choices") or [{}])[0]
    usage = data.get("usage") or {}
    # Se traduce al formato de Ollama para que orchestrator.py no tenga que distinguir el camino.
    return {
        "message": choice.get("message", {}),
        "prompt_eval_count": usage.get("prompt_tokens", 0),
        "eval_count": usage.get("completion_tokens", 0),
    }


async def embed(text: str, api_key: str | None = None) -> list[float]:
    if LLM_GATEWAY_URL:
        return await _embed_gateway(text, api_key)
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": text},
            )
            r.raise_for_status()
            return r.json().get("embedding", [])
    except httpx.HTTPError as exc:
        raise ModelUnavailableError(f"El modelo de embeddings '{EMBED_MODEL}' no está disponible") from exc


async def _embed_gateway(text: str, api_key: str | None) -> list[float]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                f"{LLM_GATEWAY_URL}/v1/embeddings",
                json={"model": GATEWAY_EMBED_ALIAS, "input": text},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as exc:
        raise ModelUnavailableError(_gateway_error_message(exc)) from exc
    except httpx.HTTPError as exc:
        raise ModelUnavailableError("El gateway no está disponible") from exc
    items = data.get("data") or []
    return items[0]["embedding"] if items else []
