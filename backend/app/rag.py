import io
import numpy as np
from pypdf import PdfReader
from sqlmodel import Session, select
from app.config import CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_CHUNKS
from app.models import KnowledgeChunk, KnowledgeDocument
from app import ollama_client


def extract_text(filename: str, raw: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return raw.decode("utf-8", errors="ignore")


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


async def ingest_document(session: Session, agent_id: int, filename: str, raw: bytes) -> KnowledgeDocument:
    text = extract_text(filename, raw)
    chunks = chunk_text(text)

    doc = KnowledgeDocument(agent_id=agent_id, filename=filename, chunk_count=len(chunks))
    session.add(doc)
    session.commit()
    session.refresh(doc)

    for idx, chunk in enumerate(chunks):
        vector = await ollama_client.embed(chunk)
        session.add(
            KnowledgeChunk(
                document_id=doc.id,
                agent_id=agent_id,
                chunk_index=idx,
                content=chunk,
                embedding=vector,
            )
        )
    session.commit()
    return doc


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = (np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


async def retrieve(session: Session, agent_id: int, query: str, k: int = TOP_K_CHUNKS) -> list[dict]:
    chunks = session.exec(select(KnowledgeChunk).where(KnowledgeChunk.agent_id == agent_id)).all()
    if not chunks:
        return []
    query_vec = await ollama_client.embed(query)
    scored = [
        {"content": c.content, "score": _cosine(query_vec, c.embedding), "chunk_index": c.chunk_index}
        for c in chunks
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]
