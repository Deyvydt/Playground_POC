from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from app.config import MAX_UPLOAD_BYTES
from app.database import get_session
from app.models import Agent, KnowledgeDocument, KnowledgeChunk, User
from app.ollama_client import ModelUnavailableError
from app.security import get_current_user, require
from app import rag

router = APIRouter(prefix="/api/agents", tags=["knowledge"])

ALLOWED_EXTENSIONS = (".txt", ".md", ".pdf")


@router.get("/{agent_id}/knowledge")
def list_knowledge(agent_id: int, session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    return session.exec(
        select(KnowledgeDocument).where(KnowledgeDocument.agent_id == agent_id).order_by(KnowledgeDocument.id.desc())
    ).all()


@router.post("/{agent_id}/knowledge", status_code=201)
async def upload_knowledge(
    agent_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _: User = Depends(require("knowledge")),
):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agente no encontrado")
    if not (file.filename or "").lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(400, "Formato no soportado. Usa PDF, TXT o MD.")
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "El archivo está vacío")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "El archivo supera el límite de 10 MB")
    try:
        return await rag.ingest_document(session, agent_id, file.filename, raw)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except ModelUnavailableError as exc:
        raise HTTPException(503, str(exc)) from exc


@router.delete("/knowledge/{document_id}")
def delete_knowledge(document_id: int, session: Session = Depends(get_session), _: User = Depends(require("knowledge"))):
    doc = session.get(KnowledgeDocument, document_id)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    chunks = session.exec(select(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)).all()
    for c in chunks:
        session.delete(c)
    session.delete(doc)
    session.commit()
    return {"ok": True}
