import pytest

NUEVO = {"name": "Agente QA", "role_prompt": "Eres un agente de pruebas.", "tools": ["calculadora"], "temperature": 0.2}


def test_listar_agentes_devuelve_los_seis_de_demostracion(client, as_role):
    r = client.get("/api/agents", headers=as_role("viewer"))
    assert r.status_code == 200
    assert {a["name"] for a in r.json()} >= {"Soporte TI", "Analista de Datos", "Asesor de Onboarding"}
    assert len(r.json()) == 6


def test_crear_agente_guarda_quien_lo_creo(client, as_role):
    r = client.post("/api/agents", json=NUEVO, headers=as_role("developer"))
    assert r.status_code == 201
    assert r.json()["created_by"] == "Carlos Vega"
    assert r.json()["tools"] == ["calculadora"]


@pytest.mark.parametrize("cambio", [
    {"name": "A"},
    {"role_prompt": "x"},
    {"temperature": 1.5},
    {"temperature": -0.1},
])
def test_crear_agente_con_datos_invalidos_responde_422(client, as_role, cambio):
    assert client.post("/api/agents", json={**NUEVO, **cambio}, headers=as_role("developer")).status_code == 422


def test_actualizar_agente_cambia_solo_lo_enviado(client, as_role):
    agent_id = client.post("/api/agents", json=NUEVO, headers=as_role("developer")).json()["id"]
    r = client.put(f"/api/agents/{agent_id}", json={"status": "inactive"}, headers=as_role("developer"))
    assert r.status_code == 200
    assert r.json()["status"] == "inactive" and r.json()["name"] == "Agente QA"
    assert r.json()["updated_at"] is not None


def test_estado_invalido_es_rechazado(client, as_role):
    assert client.put("/api/agents/1", json={"status": "borrado"}, headers=as_role("admin")).status_code == 422


@pytest.mark.parametrize("method, path", [("get", "/api/agents/999"), ("put", "/api/agents/999"), ("delete", "/api/agents/999")])
def test_agente_inexistente_responde_404(client, as_role, method, path):
    kwargs = {"json": {"name": "Otro"}} if method == "put" else {}
    assert getattr(client, method)(path, headers=as_role("admin"), **kwargs).status_code == 404


def test_eliminar_agente_borra_conversaciones_y_documentos_pero_conserva_el_consumo(client, as_role):
    admin = as_role("admin")
    agent_id = client.post("/api/agents", json=NUEVO, headers=admin).json()["id"]
    client.post(f"/api/agents/{agent_id}/chat", json={"message": "hola"}, headers=admin)
    client.post(f"/api/agents/{agent_id}/knowledge", files={"file": ("a.txt", b"contenido de prueba")}, headers=admin)

    assert client.delete(f"/api/agents/{agent_id}", headers=admin).json() == {"ok": True}

    assert client.get(f"/api/agents/{agent_id}/conversations", headers=admin).json() == []
    assert client.get(f"/api/agents/{agent_id}/knowledge", headers=admin).json() == []
    resumen = client.get("/api/metrics/summary", headers=admin).json()
    assert any(row["agent_name"] == "Agente QA" for row in resumen["agents_breakdown"])


@pytest.mark.parametrize("path", ["/api/agents/9223372036854775808", "/api/users/9223372036854775808"])
def test_id_fuera_del_rango_de_la_base_responde_404_y_no_500(client, as_role, path):
    """Regresión: Schemathesis encontró un 500 (OverflowError de SQLite) con ids enormes."""
    assert client.put(path, json={}, headers=as_role("admin")).status_code == 404
