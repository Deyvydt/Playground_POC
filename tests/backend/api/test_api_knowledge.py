import pytest

from app.routers import knowledge


def upload(client, headers, agent_id, name, content):
    return client.post(f"/api/agents/{agent_id}/knowledge", files={"file": (name, content)}, headers=headers)


def test_subir_documento_lo_fragmenta_y_lo_lista(client, as_role):
    dev = as_role("developer")
    r = upload(client, dev, 5, "politicas.txt", ("Politica de teletrabajo. " * 100).encode())
    assert r.status_code == 201
    assert r.json()["chunk_count"] >= 2
    assert [d["filename"] for d in client.get("/api/agents/5/knowledge", headers=dev).json()] == ["politicas.txt"]


@pytest.mark.parametrize("name, content, status, detail", [
    ("vacio.txt", b"", 400, "El archivo está vacío"),
    ("datos.csv", b"a,b", 400, "Formato no soportado. Usa PDF, TXT o MD."),
    ("espacios.md", b"   \n  ", 400, "El documento no contiene texto legible"),
])
def test_documentos_invalidos_son_rechazados_con_motivo(client, as_role, name, content, status, detail):
    r = upload(client, as_role("developer"), 5, name, content)
    assert (r.status_code, r.json()["detail"]) == (status, detail)


def test_documento_que_supera_el_limite_responde_413(client, as_role, monkeypatch):
    monkeypatch.setattr(knowledge, "MAX_UPLOAD_BYTES", 10)
    assert upload(client, as_role("developer"), 5, "grande.txt", b"x" * 11).status_code == 413


def test_subir_a_un_agente_inexistente_responde_404(client, as_role):
    assert upload(client, as_role("developer"), 999, "a.txt", b"hola").status_code == 404


def test_si_fallan_los_embeddings_responde_503(client, as_role, fake_llm):
    fake_llm.failure = "El modelo de embeddings no está disponible"
    assert upload(client, as_role("developer"), 5, "a.txt", b"hola mundo").status_code == 503


def test_viewer_no_puede_gestionar_conocimiento(client, as_role):
    assert upload(client, as_role("viewer"), 5, "a.txt", b"hola").status_code == 403
    assert client.delete("/api/agents/knowledge/1", headers=as_role("viewer")).status_code == 403


def test_eliminar_documento_quita_sus_fragmentos(client, as_role, db):
    from sqlmodel import select
    from app.models import KnowledgeChunk
    dev = as_role("developer")
    doc_id = upload(client, dev, 5, "a.txt", b"contenido temporal de prueba").json()["id"]
    assert client.delete(f"/api/agents/knowledge/{doc_id}", headers=dev).json() == {"ok": True}
    assert db.exec(select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id)).all() == []
    assert client.delete(f"/api/agents/knowledge/{doc_id}", headers=dev).status_code == 404
