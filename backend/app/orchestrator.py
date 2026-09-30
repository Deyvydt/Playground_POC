import json
import time
from sqlmodel import Session
from app.models import Agent, MetricLog
from app import ollama_client, rag, tools

MAX_TOOL_ROUNDS = 3


async def run_agent_turn(session: Session, agent: Agent, history: list[dict], user_message: str) -> dict:
    """Ejecuta un turno completo del agente: RAG -> LLM -> (tool-calls) -> respuesta final.

    Devuelve un dict con: content, trace (pasos), latency_ms, prompt_tokens, completion_tokens
    """
    t0 = time.perf_counter()
    trace: list[dict] = []

    system_prompt = agent.role_prompt
    retrieved = await rag.retrieve(session, agent.id, user_message)
    if retrieved:
        context_block = "\n\n".join(f"[Fragmento {i+1}] {r['content']}" for i, r in enumerate(retrieved))
        system_prompt = (
            f"{agent.role_prompt}\n\n"
            "Usa el siguiente contexto recuperado de la base de conocimiento interna si es relevante:\n"
            f"{context_block}"
        )
        trace.append({
            "type": "retrieval",
            "title": f"RAG: {len(retrieved)} fragmento(s) recuperado(s)",
            "detail": [{"score": round(r["score"], 3), "preview": r["content"][:160]} for r in retrieved],
        })

    messages = [{"role": "system", "content": system_prompt}, *history, {"role": "user", "content": user_message}]
    trace.append({"type": "system_prompt", "title": "Prompt de sistema", "detail": system_prompt})

    tool_defs = tools.definitions_for(agent.tools) if agent.tools else None
    prompt_tokens = 0
    completion_tokens = 0
    tool_call_count = 0

    final_text = ""
    for _round in range(MAX_TOOL_ROUNDS):
        result = await ollama_client.chat(agent.model, messages, agent.temperature, tool_defs)
        message = result.get("message", {})
        prompt_tokens += result.get("prompt_eval_count", 0)
        completion_tokens += result.get("eval_count", 0)

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
    latency_ms = int((time.perf_counter() - t0) * 1000)

    session.add(MetricLog(
        agent_id=agent.id,
        agent_name=agent.name,
        model=agent.model,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        tool_calls=tool_call_count,
        success=True,
    ))
    session.commit()

    return {
        "content": final_text,
        "trace": trace,
        "latency_ms": latency_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
