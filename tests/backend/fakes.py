"""Doble del motor de modelos (Ollama o gateway) para probar el backend sin servicios externos."""
import math
import re
import unicodedata
import zlib

from app.ollama_client import ModelUnavailableError

EMBED_DIMS = 256
PROMPT_TOKENS = 10
COMPLETION_TOKENS = 5


def _words(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return [w for w in re.findall(r"[a-z0-9]+", text) if len(w) > 2]


def bag_of_words(text: str) -> list[float]:
    """Embedding determinista: textos que comparten palabras quedan cerca (la similitud coseno funciona)."""
    vector = [0.0] * EMBED_DIMS
    for word in _words(text):
        vector[zlib.crc32(word.encode()) % EMBED_DIMS] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


class FakeLLM:
    """Responde en el formato de Ollama. Las respuestas se encolan; sin cola, devuelve un texto genérico."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.replies: list[dict] = []
        self.calls: list[dict] = []
        self.embed_calls: list[dict] = []
        self.available = True
        self.failure: str | None = None

    def reply(self, content: str) -> None:
        self.replies.append({"role": "assistant", "content": content})

    def tool_call(self, name: str, arguments: dict) -> None:
        self.replies.append({"role": "assistant", "content": "", "tool_calls": [{"function": {"name": name, "arguments": arguments}}]})

    async def chat(self, model, messages, temperature=0.4, tools=None, api_key=None, metadata=None):
        self.calls.append({"model": model, "messages": messages, "tools": tools, "api_key": api_key, "metadata": metadata})
        if self.failure:
            raise ModelUnavailableError(self.failure)
        message = self.replies.pop(0) if self.replies else {"role": "assistant", "content": f"Respuesta simulada a: {messages[-1]['content'][:60]}"}
        return {"message": message, "prompt_eval_count": PROMPT_TOKENS, "eval_count": COMPLETION_TOKENS}

    async def embed(self, text, api_key=None, metadata=None):
        self.embed_calls.append({"text": text, "api_key": api_key, "metadata": metadata})
        if self.failure:
            raise ModelUnavailableError(self.failure)
        return bag_of_words(text)

    async def is_available(self):
        return self.available

    async def list_models(self):
        return [
            {"name": "modelo-prueba:latest", "size": 1, "details": {"family": "llama", "parameter_size": "3B"}},
            {"name": "embed-prueba:latest", "size": 1, "details": {"family": "bert", "parameter_size": "137M"}},
        ]

    @property
    def last_system_prompt(self) -> str:
        return self.calls[-1]["messages"][0]["content"]
