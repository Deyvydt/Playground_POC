import pytest


def test_health_informa_el_estado_del_gateway(client, gateway):
    assert client.get("/gov/health").json() == {"status": "ok", "gateway_available": True}
    gateway.down = True
    assert client.get("/gov/health").json()["gateway_available"] is False


def test_areas_con_gasto_presupuesto_y_conteos(client, headers, gateway):
    from support import registrar
    admin = headers("admin")
    gateway.teams["rrhh"] = {"spend": 2.0, "max_budget": 8.0}
    agent_id = registrar(client, admin, "Uno", "talentia").json()["agent"]["id"]
    registrar(client, admin, "Dos", "talentia")
    client.post(f"/gov/agents/{agent_id}/pause", json={"reason": "x"}, headers=admin)
    rrhh = next(a for a in client.get("/gov/areas", headers=headers("viewer")).json() if a["id"] == "rrhh")
    assert (rrhh["agentes"], rrhh["agentes_pausados"], rrhh["sistemas"]) == (2, 1, 1)
    assert rrhh["usage"]["budget_ratio"] == 0.25 and rrhh["organization"] == "TCS"


def test_areas_sin_gateway_siguen_respondiendo(client, headers, gateway):
    gateway.down = True
    areas = client.get("/gov/areas", headers=headers("viewer")).json()
    assert len(areas) == 3 and all(a["usage"] == {"available": False} for a in areas)


@pytest.mark.particion
def test_crear_sistema(client, headers):
    r = client.post("/gov/sistemas", json={"name": "Cobranzas IA", "area_id": "plataforma"}, headers=headers("admin"))
    assert r.status_code == 201 and r.json()["slug"] == "cobranzas-ia"
    assert client.post("/gov/sistemas", json={"name": "Cobranzas IA", "area_id": "plataforma"}, headers=headers("admin")).status_code == 409
    assert client.post("/gov/sistemas", json={"name": "Otro", "area_id": "inexistente"}, headers=headers("admin")).status_code == 404
    assert client.post("/gov/sistemas", json={"name": "Otro", "area_id": "rrhh"}, headers=headers("viewer")).status_code == 403
    nombres = [s["name"] for s in client.get("/gov/sistemas", headers=headers("viewer")).json()]
    assert "Cobranzas IA" in nombres


def test_notificaciones_contador_y_marcar_leidas(client, headers):
    from support import registrar
    admin = headers("admin")
    registrar(client, admin, "Uno")
    registrar(client, admin, "Dos")
    data = client.get("/gov/notifications", headers=headers("viewer")).json()
    assert data["unread"] == 2 and data["items"][0]["title"] == "Agente registrado: Dos"
    client.post(f"/gov/notifications/{data['items'][0]['id']}/read", headers=headers("viewer"))
    assert client.get("/gov/notifications?unread_only=true", headers=admin).json()["unread"] == 1
    client.post("/gov/notifications/read-all", headers=admin)
    assert client.get("/gov/notifications", headers=admin).json()["unread"] == 0
    assert client.post("/gov/notifications/999/read", headers=admin).status_code == 404


def test_webhook_de_alertas(client, headers, gateway):
    from support import agente, avisos, registrar
    agent_id = registrar(client, headers("admin")).json()["agent"]["id"]
    token = "token-webhook-pruebas"
    assert client.post("/gov/alerts/gateway?token=malo", json={}).status_code == 401
    r = client.post(f"/gov/alerts/gateway?token={token}", json={
        "event": "threshold_crossed", "event_message": "80% del presupuesto", "spend": 0.8, "max_budget": 1.0,
        "token": agente(agent_id).key_hash})
    assert r.json() == {"ok": True}
    aviso = avisos("alerta_gateway")[0]
    assert aviso.severity == "warning" and aviso.agente_id == agent_id
    client.post(f"/gov/alerts/gateway?token={token}", json={"event": "budget_crossed", "token": agente(agent_id).key_hash})
    assert agente(agent_id).status == "pausado"


@pytest.mark.regresion
@pytest.mark.adivinanza_errores
def test_webhook_rechaza_tokens_no_ascii_y_cuerpos_invalidos_sin_error_del_servidor(client):
    """Regresión: Schemathesis encontró un 500 con un token no ASCII."""
    assert client.post("/gov/alerts/gateway?token=tókenñ", json={}).status_code == 401
    ok = "token-webhook-pruebas"
    assert client.post(f"/gov/alerts/gateway?token={ok}", content=b"no es json").status_code == 400
    assert client.post(f"/gov/alerts/gateway?token={ok}", json=[1, 2]).status_code == 400
