from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Agent, Conversation, Message, User
from app.ollama_client import ModelUnavailableError
from app.schemas import ChatRequest
from app.orchestrator import run_agent_turn
from app.security import get_current_user

router = APIRouter(prefix="/api", tags=["chat"])


def _own_conversation(session: Session, conversation_id: int, user: User) -> Conversation:
    conversation = session.get(Conversation, conversation_id)
    if not conversation or (conversation.user_id not in (None, user.id) and user.role != "admin"):
        raise HTTPException(404, "Conversación no encontrada")
    return conversation


@router.get("/agents/{agent_id}/conversations")
def list_conversations(agent_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return session.exec(
        select(Conversation)
        .where(Conversation.agent_id == agent_id, Conversation.user_id == user.id)
        .order_by(Conversation.id.desc())
    ).all()


@router.get("/conversations/{conversation_id}/messages")
def list_messages(conversation_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    _own_conversation(session, conversation_id, user)
    return session.exec(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
    ).all()


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    conversation = _own_conversation(session, conversation_id, user)
    for msg in session.exec(select(Message).where(Message.conversation_id == conversation_id)).all():
        session.delete(msg)
    session.delete(conversation)
    session.commit()
    return {"ok": True}


@router.post("/agents/{agent_id}/chat")
async def chat_with_agent(
    agent_id: int, payload: ChatRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)
):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agente no encontrado")
    if agent.status != "active":
        raise HTTPException(409, "Este agente está pausado")

    if payload.conversation_id:
        conversation = _own_conversation(session, payload.conversation_id, user)
    else:
        conversation = Conversation(agent_id=agent_id, user_id=user.id, title=payload.message[:60])
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

    history_rows = session.exec(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.id)
    ).all()
    history = [{"role": m.role, "content": m.content} for m in history_rows]

    session.add(Message(conversation_id=conversation.id, role="user", content=payload.message))
    session.commit()

    try:
        result = await run_agent_turn(session, agent, history, payload.message, user_id=user.id)
    except ModelUnavailableError as exc:
        raise HTTPException(503, str(exc)) from exc

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
