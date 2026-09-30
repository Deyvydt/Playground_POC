from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from app.database import get_session
from app.models import Agent, KnowledgeDocument, KnowledgeChunk
from app import rag

router = APIRouter(prefix="/api/agents", tags=["knowledge"])


@router.get("/{agent_id}/knowledge")
def list_knowledge(agent_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(KnowledgeDocument).where(KnowledgeDocument.agent_id == agent_id)
    ).all()


@router.post("/{agent_id}/knowledge")
async def upload_knowledge(agent_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agente no encontrado")
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Archivo vacio")
    doc = await rag.ingest_document(session, agent_id, file.filename, raw)
    return doc


@router.delete("/knowledge/{document_id}")
def delete_knowledge(document_id: int, session: Session = Depends(get_session)):
    doc = session.get(KnowledgeDocument, document_id)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    chunks = session.exec(select(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)).all()
    for c in chunks:
        session.delete(c)
    session.delete(doc)
    session.commit()
    return {"ok": True}
