import pytest


def test_ejecutar_talentia_devuelve_traza_y_resultado(client, user, model):
    model.respond("evaluador_ajuste", "90")
    r = client.post("/lab/runs/talentia", json={"cv": "Ana, Java", "vacante": "Java Senior"}, headers=user)
    assert r.status_code == 200
    body = r.json()
    assert body["sistema"] == "talentia" and body["error"] is None and len(body["run_id"]) == 36
    assert [p["nodo"] for p in body["trace"]] == ["analizador_cv", "evaluador_ajuste", "generador_entrevista"]
    assert body["resultado"]["puntaje"] == 90
    assert "trace" not in body["resultado"] and "run_id" not in body["resultado"]


@pytest.mark.particion
@pytest.mark.parametrize("sistema, payload", [
    ("talentia", {"cv": "", "vacante": "x"}),
    ("talentia", {"cv": "x", "vacante": "   "}),
    ("agentfactory", {"requerimiento": ""}),
])
def test_entradas_incompletas_responden_422(client, user, sistema, payload):
    assert client.post(f"/lab/runs/{sistema}", json=payload, headers=user).status_code == 422


@pytest.mark.particion
def test_sistema_desconocido_responde_404(client, user):
    assert client.post("/lab/runs/cobranzas", json={}, headers=user).status_code == 404


def test_sin_sesion_responde_401(client):
    assert client.post("/lab/runs/talentia", json={"cv": "a", "vacante": "b"}).status_code == 401


def test_health(client):
    assert client.get("/lab/health").json() == {"status": "ok"}


def test_cada_ejecucion_tiene_su_propia_traza(client, user, model):
    client.post("/lab/runs/agentfactory", json={"requerimiento": "a"}, headers=user)
    client.post("/lab/runs/agentfactory", json={"requerimiento": "b"}, headers=user)
    assert len({c["metadata"]["trace_id"] for c in model.calls}) == 2
