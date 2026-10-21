import json
import time
import uuid
from sqlmodel import Session
from app.models import Agent, MetricLog
from app import gateway_keys, ollama_client, rag, tools
from app.ollama_client import ModelUnavailableError

MAX_TOOL_ROUNDS = 3
GATEWAY_SISTEMA = "tokenio"
GATEWAY_AREA = "plataforma"


def trace_metadata(agent: Agent, trace_id: str, trace_name: str, generation_name: str, session_id: str | None) -> dict:
    """Metadatos que el gateway reenvía a Langfuse: agrupan las llamadas de un turno o flujo en una traza."""
    metadata = {
        "trace_id": trace_id,
        "trace_name": trace_name,
        "generation_name": generation_name,
        "tags": [f"agent:{agent.name}", f"area:{GATEWAY_AREA}", f"sistema:{GATEWAY_SISTEMA}"],
    }
    if session_id:
        metadata["session_id"] = session_id
    return metadata


def new_trace_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


async def run_agent_turn(
    session: Session,
    agent: Agent,
    history: list[dict],
    user_message: str,
    user_id: int | None = None,
    trace_id: str | None = None,
    trace_name: str = "chat",
    session_id: str | None = None,
) -> dict:
    """Ejecuta un turno completo del agente: RAG -> LLM -> (tool-calls) -> respuesta final.

    Devuelve un dict con: content, trace (pasos), latency_ms, prompt_tokens, completion_tokens.
    Si el motor de modelos falla, registra la metrica como fallida y relanza ModelUnavailableError.
    """
    t0 = time.perf_counter()
    trace: list[dict] = []
    prompt_tokens = 0
    completion_tokens = 0
    tool_call_count = 0

    def log_metric(success: bool, error: str | None = None) -> int:
        latency = int((time.perf_counter() - t0) * 1000)
        session.add(MetricLog(
            agent_id=agent.id,
            agent_name=agent.name,
            user_id=user_id,
            model=agent.model,
            latency_ms=latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            tool_calls=tool_call_count,
            success=success,
            error_message=error,
        ))
        session.commit()
        return latency

    api_key = gateway_keys.api_key_for(agent)
    trace_id = trace_id or new_trace_id("chat")

    def metadata_for(step: str) -> dict:
        return trace_metadata(agent, trace_id, trace_name, f"{agent.name} · {step}", session_id)

    system_prompt = agent.role_prompt
    try:
        retrieved = await rag.retrieve(session, agent.id, user_message, api_key=api_key, metadata=metadata_for("recuperación"))
    except ModelUnavailableError as exc:
        # Sin embeddings el agente aun puede responder; se deja constancia en la traza.
        retrieved = []
        trace.append({"type": "retrieval", "title": "Conocimiento no disponible", "detail": [], "error": str(exc)})
    if retrieved:
        context_block = "\n\n".join(f"[Fragmento {i+1}] {r['content']}" for i, r in enumerate(retrieved))
        system_prompt = (
            f"{agent.role_prompt}\n\n"
            "Usa el siguiente contexto recuperado de la base de conocimiento interna si es relevante:\n"
            f"{context_block}"
        )
        trace.append({
            "type": "retrieval",
            "title": f"{len(retrieved)} fragmento(s) recuperado(s)",
            "detail": [{"score": round(r["score"], 3), "preview": r["content"][:160]} for r in retrieved],
        })

    messages = [{"role": "system", "content": system_prompt}, *history, {"role": "user", "content": user_message}]
    trace.append({"type": "system_prompt", "title": "Instrucciones del sistema", "detail": system_prompt})

    tool_defs = tools.definitions_for(agent.tools) if agent.tools else None
    final_text = ""
    for round_idx in range(MAX_TOOL_ROUNDS):
        call_t0 = time.perf_counter()
        try:
            result = await ollama_client.chat(
                agent.model, messages, agent.temperature, tool_defs,
                api_key=api_key, metadata=metadata_for(f"ronda {round_idx + 1}"),
            )
        except ModelUnavailableError as exc:
            log_metric(False, str(exc))
            raise
        message = result.get("message", {})
        round_prompt = result.get("prompt_eval_count", 0)
        round_completion = result.get("eval_count", 0)
        prompt_tokens += round_prompt
        completion_tokens += round_completion
        trace.append({
            "type": "model_call",
            "title": f"Llamada al modelo {agent.model}",
            "detail": {
                "ronda": round_idx + 1,
                "tokens_entrada": round_prompt,
                "tokens_salida": round_completion,
                "latencia_ms": int((time.perf_counter() - call_t0) * 1000),
            },
        })

        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            messages.append(message)
            for call in tool_calls:
                fn = call.get("function", {})
                name = fn.get("name")
                raw_args = fn.get("arguments", {})
                args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args or "{}")
                tool_result = tools.execute_tool(name, args)
                tool_call_count += 1
                trace.append({
                    "type": "tool_call",
                    "title": f"Herramienta: {name}",
                    "detail": {"argumentos": args, "resultado": tool_result},
                })
                messages.append({"role": "tool", "content": json.dumps(tool_result, ensure_ascii=False)})
            continue

        final_text = message.get("content", "")
        break

    trace.append({"type": "final_answer", "title": "Respuesta final", "detail": final_text})
    latency_ms = log_metric(True)

    return {
        "content": final_text,
        "trace": trace,
        "latency_ms": latency_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
