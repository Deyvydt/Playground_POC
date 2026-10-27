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
    area = SISTEMA_AREA[sistema]
    # trace_id = run_id: en Langfuse cada ejecución del grafo es una traza y cada nodo una generación.
    # "agent_id" está reservado por LiteLLM (columna de texto en sus logs de gasto): con un número,
    # Postgres rechaza la fila y la llamada desaparece de la actividad y del monitor de errores.
    metadata = {
        "tokenio_agent_id": agente_id,
        "sistema": sistema,
        "area": area,
        "run_id": run_id,
        "trace_id": run_id,
        "trace_name": f"{sistema} · grafo",
        "generation_name": nodo,
        "tags": [f"agent:{agente_id}", f"area:{area}", f"sistema:{sistema}"],
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
