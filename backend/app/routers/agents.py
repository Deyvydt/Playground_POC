from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Agent, Conversation, KnowledgeChunk, KnowledgeDocument, Message, User
from app.schemas import AgentCreate, AgentUpdate
from app.security import get_current_user, require

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _get_or_404(session: Session, agent_id: int) -> Agent:
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agente no encontrado")
    return agent


@router.get("")
def list_agents(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    return session.exec(select(Agent).order_by(Agent.id)).all()


@router.post("", status_code=201)
def create_agent(payload: AgentCreate, session: Session = Depends(get_session), user: User = Depends(require("create"))):
    agent = Agent(**payload.model_dump(), created_by=user.name)
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


@router.get("/{agent_id}")
def get_agent(agent_id: int, session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    return _get_or_404(session, agent_id)


@router.put("/{agent_id}")
def update_agent(
    agent_id: int, payload: AgentUpdate, session: Session = Depends(get_session), _: User = Depends(require("edit"))
):
    agent = _get_or_404(session, agent_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(agent, key, value)
    agent.updated_at = datetime.utcnow()
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


@router.delete("/{agent_id}")
def delete_agent(agent_id: int, session: Session = Depends(get_session), _: User = Depends(require("delete"))):
    agent = _get_or_404(session, agent_id)
    # SQLite no aplica ON DELETE CASCADE por defecto: se limpian las dependencias a mano.
    conversations = session.exec(select(Conversation).where(Conversation.agent_id == agent_id)).all()
    for conv in conversations:
        for msg in session.exec(select(Message).where(Message.conversation_id == conv.id)).all():
            session.delete(msg)
        session.delete(conv)
    # Las metricas se conservan (guardan agent_name) para no alterar el historico de consumo.
    for model in (KnowledgeChunk, KnowledgeDocument):
        for row in session.exec(select(model).where(model.agent_id == agent_id)).all():
            session.delete(row)
    session.delete(agent)
    session.commit()
    return {"ok": True}
