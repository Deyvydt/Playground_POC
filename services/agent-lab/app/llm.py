"""Único punto de contacto de agent-lab con el gateway: cada nodo invoca con su propia
virtual key (nunca una master key), vía el cliente OpenAI-compatible de LangChain.
"""
import openai
from langchain_openai import ChatOpenAI
from app import secrets
from app.config import GATEWAY_URL

MODEL_ALIAS = "llama-local"
SISTEMA_AREA = {"talentia": "rrhh", "agentfactory": "desarrollo"}


def _mensaje_error(exc: Exception) -> str:
    if isinstance(exc, openai.AuthenticationError):
        return "El agente está pausado por un administrador."
    if isinstance(exc, (openai.BadRequestError, openai.RateLimitError, openai.PermissionDeniedError)):
        return "El agente agotó su presupuesto o límite de uso."
    if isinstance(exc, openai.APIConnectionError):
        return "El gateway no está disponible."
    status = getattr(exc, "status_code", None)
    return f"El gateway rechazó la llamada ({status or 'sin conexión'})."


async def call_node(sistema: str, nodo: str, system_prompt: str, human_content: str, run_id: str) -> tuple[str, dict]:
    """Invoca el LLM del nodo. Devuelve (texto_respuesta, paso_de_traza)."""
    agente_id, key = secrets.get_credential(sistema, nodo)
    llm = ChatOpenAI(base_url=f"{GATEWAY_URL}/v1", api_key=key, model=MODEL_ALIAS, temperature=0.2)
    metadata = {
        "agent_id": agente_id,
        "sistema": sistema,
        "area": SISTEMA_AREA[sistema],
        "run_id": run_id,
        "generation_name": nodo,
    }
    try:
        respuesta = await llm.ainvoke(
            [{"role": "system", "content": system_prompt}, {"role": "user", "content": human_content}],
            extra_body={"metadata": metadata},
        )
    except openai.APIError as exc:
        return "", {"nodo": nodo, "estado": "error", "entrada": human_content[:300], "mensaje": _mensaje_error(exc)}
    texto = (respuesta.content or "").strip()
    uso = respuesta.response_metadata.get("token_usage", {}) if respuesta.response_metadata else {}
    paso = {
        "nodo": nodo,
        "estado": "ok",
        "entrada": human_content[:300],
        "salida": texto[:500],
        "tokens_entrada": uso.get("prompt_tokens"),
        "tokens_salida": uso.get("completion_tokens"),
    }
    return texto, paso
