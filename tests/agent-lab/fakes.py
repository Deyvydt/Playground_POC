"""Doble de ChatOpenAI (LangChain) para ejecutar los grafos sin gateway ni modelo."""
from types import SimpleNamespace

import httpx
import openai

_REQUEST = httpx.Request("POST", "http://gateway.test/v1/chat/completions")


def gateway_error(status: int) -> openai.APIError:
    """Errores que el SDK de OpenAI lanza cuando el gateway rechaza una llamada."""
    if status == 0:
        return openai.APIConnectionError(request=_REQUEST)
    cls = {400: openai.BadRequestError, 401: openai.AuthenticationError, 403: openai.PermissionDeniedError,
           429: openai.RateLimitError}.get(status, openai.InternalServerError)
    return cls(f"HTTP {status}", response=httpx.Response(status, request=_REQUEST), body=None)


class FakeChatModel:
    """Registro compartido de llamadas y respuestas por nodo (generation_name)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.calls: list[dict] = []
        self.responses: dict[str, list] = {}

    def respond(self, nodo: str, *outputs):
        self.responses.setdefault(nodo, []).extend(outputs)

    def fail(self, nodo: str, status: int):
        self.responses.setdefault(nodo, []).append(gateway_error(status))

    def factory(self, **kwargs):
        return _FakeChat(self, kwargs)

    @property
    def path(self) -> list[str]:
        return [c["nodo"] for c in self.calls]


class _FakeChat:
    def __init__(self, registry: FakeChatModel, kwargs: dict):
        self.registry = registry
        self.kwargs = kwargs

    async def ainvoke(self, messages, extra_body=None):
        metadata = (extra_body or {}).get("metadata", {})
        nodo = metadata.get("generation_name", "?")
        self.registry.calls.append({"nodo": nodo, "messages": messages, "metadata": metadata, **self.kwargs})
        queue = self.registry.responses.get(nodo)
        output = queue.pop(0) if queue else f"Salida simulada de {nodo}"
        if isinstance(output, Exception):
            raise output
        return SimpleNamespace(content=output, response_metadata={"token_usage": {"prompt_tokens": 11, "completion_tokens": 7}})
