import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from app.database import engine, get_session
from app.models import Agent, User
from app.ollama_client import ModelUnavailableError
from app.schemas import OrchestrationRequest
from app.orchestrator import run_agent_turn
from app.security import get_current_user

router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])


def _next_input(original: str, agent: Agent, output: str) -> str:
    return (
        f"Tarea original del usuario: {original}\n\n"
        f"Resultado del agente anterior ({agent.name}):\n{output}\n\n"
        "Continua el flujo de trabajo a partir de este resultado."
    )


def _step(agent: Agent, result: dict) -> dict:
    return {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "icon": agent.icon,
        "output": result["content"],
        "trace": result["trace"],
        "latency_ms": result["latency_ms"],
        "tokens": result["prompt_tokens"] + result["completion_tokens"],
    }


def _load_pipeline(session: Session, ids: list[int]) -> list[Agent]:
    agents = []
    for agent_id in ids:
        agent = session.get(Agent, agent_id)
        if not agent:
            raise HTTPException(404, f"Agente {agent_id} no encontrado")
        agents.append(agent)
    return agents


@router.post("/run")
async def run_pipeline(
    payload: OrchestrationRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)
):
    steps = []
    running_input = payload.input_text
    for agent in _load_pipeline(session, payload.pipeline):
        try:
            result = await run_agent_turn(session, agent, [], running_input, user_id=user.id)
        except ModelUnavailableError as exc:
            raise HTTPException(503, str(exc)) from exc
        steps.append(_step(agent, result))
        running_input = _next_input(payload.input_text, agent, result["content"])
    return {"steps": steps, "final_output": steps[-1]["output"] if steps else ""}


@router.post("/stream")
async def stream_pipeline(payload: OrchestrationRequest, user: User = Depends(get_current_user)):
    """Igual que /run, pero emite un evento NDJSON por paso para mostrar el progreso en vivo."""
    user_id = user.id
    with Session(engine) as check:
        _load_pipeline(check, payload.pipeline)

    async def events():
        # La sesion de Depends se cierra antes de que empiece el streaming: se abre una propia.
        with Session(engine) as session:
            running_input = payload.input_text
            for index, agent_id in enumerate(payload.pipeline):
                agent = session.get(Agent, agent_id)
                yield json.dumps({"event": "start", "index": index, "agent_id": agent.id}) + "\n"
                try:
                    result = await run_agent_turn(session, agent, [], running_input, user_id=user_id)
                except ModelUnavailableError as exc:
                    yield json.dumps({"event": "error", "index": index, "message": str(exc)}) + "\n"
                    return
                yield json.dumps({"event": "step", "index": index, "step": _step(agent, result)}, ensure_ascii=False) + "\n"
                running_input = _next_input(payload.input_text, agent, result["content"])
            yield json.dumps({"event": "done"}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")
