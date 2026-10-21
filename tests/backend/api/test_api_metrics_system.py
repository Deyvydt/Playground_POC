import pytest


def conversar(client, headers, agent_id, veces):
    for i in range(veces):
        client.post(f"/api/agents/{agent_id}/chat", json={"message": f"m{i}"}, headers=headers)


def test_resumen_suma_solicitudes_tokens_errores_y_costos(client, as_role, fake_llm):
    dev = as_role("developer")
    conversar(client, dev, 1, 2)
    fake_llm.failure = "caído"
    conversar(client, dev, 1, 1)
    r = client.get("/api/metrics/summary?days=7", headers=dev).json()
    assert (r["total_requests"], r["total_tokens"], r["prompt_tokens"], r["completion_tokens"]) == (3, 30, 20, 10)
    assert r["error_rate"] == pytest.approx(1 / 3, abs=1e-4)
    assert r["local_cost_usd"] == 0.0
    assert r["estimated_cloud_cost_usd"] == round(30 / 1000 * r["cloud_price_per_1k"], 4)
    assert r["users_breakdown"][0]["name"] == "Carlos Vega"
    assert r["total_agents"] == 6 and r["active_agents"] == 5  # "Revisor de Contratos" se siembra inactivo


def test_resumen_sin_actividad_no_divide_por_cero(client, as_role):
    r = client.get("/api/metrics/summary", headers=as_role("developer")).json()
    assert (r["total_requests"], r["avg_latency_ms"], r["error_rate"]) == (0, 0, 0)


def test_serie_temporal_tiene_un_punto_por_dia_y_filtra_por_agente(client, as_role):
    dev = as_role("developer")
    conversar(client, dev, 1, 2)
    conversar(client, dev, 2, 1)
    serie = client.get("/api/metrics/timeseries?days=5", headers=dev).json()
    assert len(serie) == 5
    assert serie[-1]["requests"] == 3
    solo_agente = client.get("/api/metrics/timeseries?days=5&agent_id=2", headers=dev).json()
    assert solo_agente[-1]["requests"] == 1


@pytest.mark.parametrize("query", ["days=0", "days=366", "days=abc"])
def test_periodos_fuera_de_rango_responden_422(client, as_role, query):
    assert client.get(f"/api/metrics/summary?{query}", headers=as_role("developer")).status_code == 422


def test_actividad_reciente_muestra_quien_uso_cada_agente(client, as_role):
    dev = as_role("developer")
    conversar(client, dev, 1, 1)
    actividad = client.get("/api/metrics/activity?limit=5", headers=dev).json()
    assert actividad[0]["user_name"] == "Carlos Vega" and actividad[0]["agent_name"] == "Soporte TI"


def test_health_informa_el_estado_del_motor_sin_sesion(client, fake_llm):
    assert client.get("/api/health").json() == {"status": "ok", "ollama_available": True}
    fake_llm.available = False
    assert client.get("/api/health").json()["ollama_available"] is False


def test_modelos_marca_cual_es_de_embeddings(client, as_role):
    modelos = {m["name"]: m["embedding"] for m in client.get("/api/models", headers=as_role("viewer")).json()}
    assert modelos == {"modelo-prueba:latest": False, "embed-prueba:latest": True}


def test_catalogo_de_herramientas_y_roles(client, as_role):
    viewer = as_role("viewer")
    assert {t["name"] for t in client.get("/api/tools", headers=viewer).json()} == {"calculadora", "fecha_actual", "consultar_ticket_interno"}
    roles = client.get("/api/roles", headers=viewer).json()
    assert roles["viewer"] == ["chat"] and "govern" in roles["admin"]
