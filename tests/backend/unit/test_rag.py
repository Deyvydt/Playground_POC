import asyncio

import pytest

from app import rag
from fakes import bag_of_words


@pytest.mark.limites
def test_chunk_text_respeta_tamano_y_solapamiento():
    texto = "a" * 2000
    fragmentos = rag.chunk_text(texto, size=800, overlap=120)
    assert [len(f) for f in fragmentos] == [800, 800, 640]
    assert fragmentos[0][-120:] == fragmentos[1][:120]


def test_chunk_text_normaliza_espacios_y_saltos_de_linea():
    assert rag.chunk_text("hola   mundo\n\n  adios") == ["hola mundo adios"]


@pytest.mark.particion
@pytest.mark.parametrize("texto", ["", "   \n\t  "])
def test_chunk_text_sin_contenido_no_genera_fragmentos(texto):
    assert rag.chunk_text(texto) == []


def test_extract_text_lee_texto_plano_en_utf8():
    assert rag.extract_text("notas.md", "Política de café ☕".encode()) == "Política de café ☕"


@pytest.mark.adivinanza_errores
def test_extract_text_ignora_bytes_invalidos():
    assert rag.extract_text("notas.txt", b"hola \xff mundo") == "hola  mundo"


def test_cosine_de_vectores_iguales_es_uno_y_de_vector_nulo_es_cero():
    v = bag_of_words("vacaciones anuales")
    assert rag._cosine(v, v) == pytest.approx(1.0)
    assert rag._cosine(v, [0.0] * len(v)) == 0.0


def test_retrieve_ordena_por_similitud(db):
    from app.models import Agent
    agent = Agent(name="RAG", role_prompt="Responde con el contexto.")
    db.add(agent)
    db.commit()
    db.refresh(agent)
    texto = ("Politica de vacaciones: quince dias al ano. " * 30) + ("Horario de oficina de nueve a seis. " * 30)
    asyncio.run(rag.ingest_document(db, agent.id, "manual.txt", texto.encode()))

    resultados = asyncio.run(rag.retrieve(db, agent.id, "cuantos dias de vacaciones tengo", k=2))

    assert len(resultados) == 2
    assert resultados[0]["score"] >= resultados[1]["score"]
    assert "vacaciones" in resultados[0]["content"].lower()


def test_retrieve_sin_documentos_no_llama_al_modelo(db, fake_llm):
    assert asyncio.run(rag.retrieve(db, 9999, "pregunta")) == []
    assert fake_llm.embed_calls == []


@pytest.mark.adivinanza_errores
def test_ingest_no_guarda_nada_si_falla_un_embedding(db, fake_llm):
    from app.models import KnowledgeDocument
    from sqlmodel import select
    antes = len(db.exec(select(KnowledgeDocument)).all())
    fake_llm.failure = "El motor de modelos no está disponible"
    with pytest.raises(Exception):
        asyncio.run(rag.ingest_document(db, 1, "doc.txt", ("texto " * 400).encode()))
    assert len(db.exec(select(KnowledgeDocument)).all()) == antes


def test_ingest_rechaza_documentos_sin_texto(db):
    with pytest.raises(ValueError, match="no contiene texto"):
        asyncio.run(rag.ingest_document(db, 1, "vacio.txt", b"   "))


@pytest.mark.limites
@pytest.mark.parametrize("largo, fragmentos", [(1, 1), (800, 1), (801, 2)])
def test_chunk_text_en_el_limite_del_tamano(largo, fragmentos):
    assert len(rag.chunk_text("a" * largo, size=800, overlap=120)) == fragmentos
