import httpx
from app.config import OLLAMA_HOST, EMBED_MODEL

TIMEOUT = httpx.Timeout(120.0, connect=10.0)


async def list_models() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            r.raise_for_status()
            data = r.json()
            return data.get("models", [])
    except httpx.HTTPError:
        return []


async def is_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            return r.status_code == 200
    except httpx.HTTPError:
        return False


async def chat(model: str, messages: list[dict], temperature: float = 0.4, tools: list[dict] | None = None) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        r.raise_for_status()
        return r.json()


async def embed(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
        )
        r.raise_for_status()
        data = r.json()
        return data.get("embedding", [])
