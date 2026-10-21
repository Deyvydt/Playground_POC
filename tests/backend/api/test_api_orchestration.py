import pytest
import json


def test_flujo_ejecuta_los_agentes_en_orden_y_devuelve_el_ultimo_resultado(client, as_role, fake_llm):
    fake_llm.reply("Paso 1")
    fake_llm.reply("Paso 2")
    r = client.post("/api/orchestration/run", json={"input_text": "Tarea", "pipeline": [2, 3]}, headers=as_role("viewer"))
    assert r.status_code == 200
    body = r.json()
    assert [s["agent_name"] for s in body["steps"]] == ["Analista de Datos", "Redactor de Reportes"]
    assert body["final_output"] == "Paso 2"
    assert body["steps"][0]["tokens"] == 15


def test_el_flujo_comparte_una_sola_traza_entre_agentes(client, as_role, fake_llm):
    client.post("/api/orchestration/run", json={"input_text": "Tarea", "pipeline": [2, 3]}, headers=as_role("viewer"))
    ids = {c["metadata"]["trace_id"] for c in fake_llm.calls}
    assert len(ids) == 1 and next(iter(ids)).startswith("flujo-")


def test_flujo_con_agente_inexistente_responde_404(client, as_role):
    r = client.post("/api/orchestration/run", json={"input_text": "x", "pipeline": [1, 999]}, headers=as_role("viewer"))
    assert r.status_code == 404


@pytest.mark.limites
def test_flujo_vacio_es_rechazado(client, as_role):
    r = client.post("/api/orchestration/run", json={"input_text": "x", "pipeline": []}, headers=as_role("viewer"))
    assert r.status_code == 422


@pytest.mark.adivinanza_errores
def test_flujo_en_vivo_emite_un_evento_de_error_y_se_detiene_si_falla_el_motor(client, as_role, fake_llm):
    fake_llm.failure = "El motor de modelos no está disponible"
    r = client.post("/api/orchestration/stream", json={"input_text": "x", "pipeline": [2, 3]}, headers=as_role("viewer"))
    eventos = [json.loads(line) for line in r.text.splitlines() if line]
    assert [e["event"] for e in eventos] == ["start", "error"]
    assert eventos[-1]["message"] == "El motor de modelos no está disponible"


def test_flujo_en_vivo_con_agente_inexistente_falla_antes_de_empezar(client, as_role):
    r = client.post("/api/orchestration/stream", json={"input_text": "x", "pipeline": [999]}, headers=as_role("viewer"))
    assert r.status_code == 404
