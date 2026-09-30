from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Agent
from app.schemas import AgentCreate, AgentUpdate

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
def list_agents(session: Session = Depends(get_session)):
    return session.exec(select(Agent).order_by(Agent.id)).all()


@router.post("")
def create_agent(payload: AgentCreate, session: Session = Depends(get_session)):
    agent = Agent(**payload.model_dump())
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


@router.get("/{agent_id}")
def get_agent(agent_id: int, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agente no encontrado")
    return agent


@router.put("/{agent_id}")
def update_agent(agent_id: int, payload: AgentUpdate, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agente no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(agent, key, value)
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


@router.delete("/{agent_id}")
def delete_agent(agent_id: int, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agente no encontrado")
    session.delete(agent)
    session.commit()
    return {"ok": True}
