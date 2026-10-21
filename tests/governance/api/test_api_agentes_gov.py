import pytest

from support import agente, avisos, registrar, sistema_id


def test_registrar_devuelve_la_key_y_la_guia_una_sola_vez(client, headers):
    r = registrar(client, headers("admin"), "Clasificador", max_budget=2.5, rpm_limit=10)
    assert r.status_code == 201
    body = r.json()
    assert body["connection"]["api_key"].startswith("sk-")
    assert set(body["connection"]) >= {"base_url", "python", "java", "curl", "models"}
    detalle = client.get(f"/gov/agents/{body['agent']['id']}", headers=headers("viewer")).json()
    assert "key_hash" not in detalle and body["connection"]["api_key"] not in str(detalle)


@pytest.mark.particion
@pytest.mark.limites
@pytest.mark.tabla_decision
@pytest.mark.parametrize("payload, status", [
    ({"name": "X", "sistema_id": 1}, 422),
    ({"name": "Valido", "sistema_id": 999}, 404),
    ({"name": "Valido", "sistema_id": 1, "runtime": "nube"}, 422),
    ({"name": "Valido", "sistema_id": 1, "max_budget": -1}, 422),
    ({"name": "Valido", "sistema_id": 1, "models": []}, 422),
])
def test_registro_invalido(client, headers, payload, status):
    assert client.post("/gov/agents", json=payload, headers=headers("admin")).status_code == status


def test_nombre_repetido_en_el_mismo_sistema_responde_409(client, headers):
    registrar(client, headers("admin"), "Duplicado")
    assert registrar(client, headers("admin"), "Duplicado").status_code == 409


def test_gateway_caido_al_registrar_responde_503(client, headers, gateway):
    gateway.down = True
    assert registrar(client, headers("admin")).status_code == 503


@pytest.mark.parametrize("role", ["developer", "viewer"])
def test_solo_admin_registra_pausa_edita_regenera_y_da_de_baja(client, headers, role):
    agent_id = registrar(client, headers("admin")).json()["agent"]["id"]
    h = headers(role)
    assert registrar(client, h, "Otro").status_code == 403
    assert client.post(f"/gov/agents/{agent_id}/pause", json={"reason": "x"}, headers=h).status_code == 403
    assert client.post(f"/gov/agents/{agent_id}/resume", headers=h).status_code == 403
    assert client.patch(f"/gov/agents/{agent_id}", json={"max_budget": 9}, headers=h).status_code == 403
    assert client.post(f"/gov/agents/{agent_id}/regenerate-key", headers=h).status_code == 403
    assert client.delete(f"/gov/agents/{agent_id}", headers=h).status_code == 403
    assert client.get(f"/gov/agents/{agent_id}", headers=h).status_code == 200


def test_sin_sesion_responde_401(client):
    assert client.get("/gov/agents").status_code == 401


def test_listado_filtra_por_area_y_sistema_e_incluye_el_uso(client, headers, gateway):
    admin = headers("admin")
    registrar(client, admin, "En RRHH", "talentia")
    registrar(client, admin, "En Desarrollo", "agentfactory")
    rrhh = client.get("/gov/agents?area_id=rrhh", headers=admin).json()
    assert [a["name"] for a in rrhh] == ["En RRHH"]
    assert rrhh[0]["usage"]["available"] is True and rrhh[0]["sistema"]["slug"] == "talentia"
    por_sistema = client.get(f"/gov/agents?sistema_id={sistema_id('agentfactory')}", headers=admin).json()
    assert [a["name"] for a in por_sistema] == ["En Desarrollo"]


@pytest.mark.transicion_estados
def test_pausar_y_reactivar(client, headers, gateway):
    admin = headers("admin")
    agent_id = registrar(client, admin).json()["agent"]["id"]
    r = client.post(f"/gov/agents/{agent_id}/pause", json={"reason": "Revisión"}, headers=admin)
    assert r.json()["status"] == "pausado" and r.json()["paused_by"] == "Usuario admin"
    r = client.post(f"/gov/agents/{agent_id}/resume", headers=admin)
    assert r.json()["status"] == "activo" and "warning" not in r.json()


@pytest.mark.transicion_estados
def test_reactivar_sin_presupuesto_avisa_que_seguira_bloqueado_por_el_gateway(client, headers, gateway):
    admin = headers("admin")
    agent_id = registrar(client, admin).json()["agent"]["id"]
    client.post(f"/gov/agents/{agent_id}/pause", json={"reason": "x"}, headers=admin)
    gateway.set_spend(agente(agent_id).key_hash, 1.5)
    assert "sin presupuesto" in client.post(f"/gov/agents/{agent_id}/resume", headers=admin).json()["warning"]


def test_editar_limites_parcialmente(client, headers, gateway):
    admin = headers("admin")
    agent_id = registrar(client, admin, rpm_limit=10).json()["agent"]["id"]
    r = client.patch(f"/gov/agents/{agent_id}", json={"max_budget": 4.0}, headers=admin)
    assert r.json()["max_budget"] == 4.0 and r.json()["rpm_limit"] == 10


def test_dar_de_baja_y_luego_404(client, headers):
    admin = headers("admin")
    agent_id = registrar(client, admin).json()["agent"]["id"]
    assert client.delete(f"/gov/agents/{agent_id}", headers=admin).status_code == 204
    assert client.get(f"/gov/agents/{agent_id}", headers=admin).status_code == 404
    assert [n.kind for n in avisos()] == ["registro", "baja"]


def test_actividad_muestra_estado_tokens_costo_y_latencia(client, headers, gateway):
    admin = headers("admin")
    agent_id = registrar(client, admin).json()["agent"]["id"]
    gateway.add_logs(agente(agent_id).key_hash, total=3, failures=1)
    actividad = client.get(f"/gov/agents/{agent_id}/activity", headers=admin).json()
    assert [a["status"] for a in actividad] == ["failure", "success", "success"]
    assert actividad[0]["prompt_tokens"] + actividad[0]["completion_tokens"] == 15
    assert actividad[0]["latency_ms"] == 250 and actividad[0]["model"] == "llama-local"


def test_detalle_incluye_el_historial_del_agente(client, headers):
    admin = headers("admin")
    agent_id = registrar(client, admin).json()["agent"]["id"]
    client.post(f"/gov/agents/{agent_id}/pause", json={"reason": "x"}, headers=admin)
    historial = client.get(f"/gov/agents/{agent_id}", headers=admin).json()["notifications"]
    assert [n["kind"] for n in historial] == ["pausa_manual", "registro"]
