import asyncio

import pytest
from sqlmodel import select

from app import orchestrator
from app.models import MetricLog
from app.ollama_client import ModelUnavailableError
from support import agent_by_name


def run_turn(db, name, message, **kwargs):
    agent = db.get(type(agent_by_name(name)), agent_by_name(name).id)
    return asyncio.run(orchestrator.run_agent_turn(db, agent, [], message, user_id=1, **kwargs))


def test_turno_simple_registra_traza_tokens_y_metrica(db, fake_llm):
    fake_llm.reply("Listo.")
    result = run_turn(db, "Redactor de Reportes", "Resume")
    assert result["content"] == "Listo."
    assert [s["type"] for s in result["trace"]] == ["system_prompt", "model_call", "final_answer"]
    assert (result["prompt_tokens"], result["completion_tokens"]) == (10, 5)
    log = db.exec(select(MetricLog)).one()
    assert log.success and log.total_tokens == 15 and log.agent_name == "Redactor de Reportes"


def test_tool_call_ejecuta_la_herramienta_y_devuelve_el_resultado_al_modelo(db, fake_llm):
    fake_llm.tool_call("calculadora", {"expresion": "6*7"})
    fake_llm.reply("Son 42.")
    result = run_turn(db, "Analista de Datos", "¿6*7?")
    tool_step = next(s for s in result["trace"] if s["type"] == "tool_call")
    assert tool_step["detail"]["resultado"]["resultado"] == 42
    segunda_llamada = fake_llm.calls[1]["messages"]
    assert segunda_llamada[-1]["role"] == "tool" and "42" in segunda_llamada[-1]["content"]
    assert db.exec(select(MetricLog)).one().tool_calls == 1


def test_tool_call_acepta_argumentos_como_texto_json(db, fake_llm):
    fake_llm.replies.append({"role": "assistant", "content": "", "tool_calls": [
        {"function": {"name": "calculadora", "arguments": '{"expresion": "1+1"}'}}]})
    fake_llm.reply("2")
    result = run_turn(db, "Analista de Datos", "1+1")
    assert any(s["type"] == "tool_call" and s["detail"]["resultado"]["resultado"] == 2 for s in result["trace"])


def test_el_bucle_de_herramientas_se_corta_en_el_maximo_de_rondas(db, fake_llm):
    for _ in range(orchestrator.MAX_TOOL_ROUNDS + 2):
        fake_llm.tool_call("fecha_actual", {})
    result = run_turn(db, "Asistente de RR.HH.", "fecha")
    llamadas = [s for s in result["trace"] if s["type"] == "model_call"]
    assert len(llamadas) == orchestrator.MAX_TOOL_ROUNDS
    assert result["trace"][-1]["type"] == "final_answer"


def test_falla_del_motor_registra_metrica_fallida_y_propaga_el_error(db, fake_llm):
    fake_llm.failure = "El motor de modelos no está disponible"
    with pytest.raises(ModelUnavailableError):
        run_turn(db, "Redactor de Reportes", "Hola")
    log = db.exec(select(MetricLog)).one()
    assert log.success is False and log.error_message == "El motor de modelos no está disponible"


def test_si_falla_la_recuperacion_el_agente_responde_igual_y_lo_deja_en_la_traza(db, fake_llm, monkeypatch):
    async def embed_roto(*args, **kwargs):
        raise ModelUnavailableError("Embeddings caídos")
    monkeypatch.setattr(orchestrator.rag.ollama_client, "embed", embed_roto)
    fake_llm.reply("Respondo sin manual.")
    result = run_turn(db, "Asesor de Onboarding", "vacaciones")
    assert result["content"] == "Respondo sin manual."
    assert result["trace"][0] == {"type": "retrieval", "title": "Conocimiento no disponible", "detail": [], "error": "Embeddings caídos"}


def test_trace_metadata_agrupa_por_traza_y_etiqueta_agente_area_y_sistema():
    agent = agent_by_name("Soporte TI")
    meta = orchestrator.trace_metadata(agent, "chat-1", "chat · Soporte TI", "Soporte TI · ronda 1", "conversacion-7")
    assert meta == {
        "trace_id": "chat-1",
        "trace_name": "chat · Soporte TI",
        "generation_name": "Soporte TI · ronda 1",
        "tags": ["agent:Soporte TI", "area:plataforma", "sistema:tokenio"],
        "session_id": "conversacion-7",
    }
    assert "session_id" not in orchestrator.trace_metadata(agent, "x", "flujo", "g", None)


def test_todas_las_llamadas_de_un_turno_comparten_la_misma_traza(db, fake_llm):
    fake_llm.tool_call("fecha_actual", {})
    fake_llm.reply("Hoy.")
    run_turn(db, "Asistente de RR.HH.", "¿Qué día es?", trace_id="flujo-123", trace_name="flujo")
    trazas = {c["metadata"]["trace_id"] for c in fake_llm.calls}
    generaciones = [c["metadata"]["generation_name"] for c in fake_llm.calls]
    assert trazas == {"flujo-123"}
    assert generaciones == ["Asistente de RR.HH. · ronda 1", "Asistente de RR.HH. · ronda 2"]
