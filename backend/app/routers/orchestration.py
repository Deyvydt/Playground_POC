from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.models import Agent
from app.schemas import OrchestrationRequest
from app.orchestrator import run_agent_turn

router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])


@router.post("/run")
async def run_pipeline(payload: OrchestrationRequest, session: Session = Depends(get_session)):
    steps = []
    running_input = payload.input_text

    for agent_id in payload.pipeline:
        agent = session.get(Agent, agent_id)
        if not agent:
            raise HTTPException(404, f"Agente {agent_id} no encontrado")

        result = await run_agent_turn(session, agent, [], running_input)
        steps.append({
            "agent_id": agent.id,
            "agent_name": agent.name,
            "avatar_emoji": agent.avatar_emoji,
            "output": result["content"],
            "trace": result["trace"],
            "latency_ms": result["latency_ms"],
        })
        running_input = (
            f"Tarea original del usuario: {payload.input_text}\n\n"
            f"Resultado del agente anterior ({agent.name}):\n{result['content']}\n\n"
            "Continua el flujo de trabajo a partir de este resultado."
        )

    final_output = steps[-1]["output"] if steps else ""
    return {"steps": steps, "final_output": final_output}
