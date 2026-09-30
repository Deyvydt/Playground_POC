from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Agent, Conversation, Message
from app.schemas import ChatRequest
from app.orchestrator import run_agent_turn

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/agents/{agent_id}/conversations")
def list_conversations(agent_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(Conversation).where(Conversation.agent_id == agent_id).order_by(Conversation.id.desc())
    ).all()


@router.get("/conversations/{conversation_id}/messages")
def list_messages(conversation_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
    ).all()


@router.post("/agents/{agent_id}/chat")
async def chat_with_agent(agent_id: int, payload: ChatRequest, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agente no encontrado")

    if payload.conversation_id:
        conversation = session.get(Conversation, payload.conversation_id)
        if not conversation:
            raise HTTPException(404, "Conversacion no encontrada")
    else:
        conversation = Conversation(agent_id=agent_id, title=payload.message[:48])
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

    history_rows = session.exec(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.id)
    ).all()
    history = [{"role": m.role, "content": m.content} for m in history_rows]

    session.add(Message(conversation_id=conversation.id, role="user", content=payload.message))
    session.commit()

    result = await run_agent_turn(session, agent, history, payload.message)

    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["content"],
        trace=result["trace"],
        latency_ms=result["latency_ms"],
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
    )
    session.add(assistant_msg)
    session.commit()
    session.refresh(assistant_msg)

    return {
        "conversation_id": conversation.id,
        "message": {"role": "assistant", "content": result["content"]},
        "trace": result["trace"],
        "latency_ms": result["latency_ms"],
        "prompt_tokens": result["prompt_tokens"],
        "completion_tokens": result["completion_tokens"],
    }
