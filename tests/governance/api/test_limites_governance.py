"""Valores límite y particiones de equivalencia de governance."""
import asyncio

import pytest

from app import monitor
from app.notify import notify
from support import agente, avisos, registrar, sistema_id


@pytest.mark.limites
@pytest.mark.parametrize("nombre, status", [("A", 422), ("AB", 201), ("N" * 80, 201), ("N" * 81, 422)])
def test_nombre_del_agente_entre_2_y_80_caracteres(client, headers, nombre, status):
    assert registrar(client, headers("admin"), nombre).status_code == status


@pytest.mark.limites
@pytest.mark.parametrize("campo, valor, status", [
    ("max_budget", -0.01, 422), ("max_budget", 0, 201),
    ("rpm_limit", 0, 422), ("rpm_limit", 1, 201),
    ("tpm_limit", 0, 422), ("tpm_limit", 1, 201),
])
def test_limites_de_presupuesto_y_uso(client, headers, campo, valor, status):
    assert registrar(client, headers("admin"), f"Agente {campo} {valor}", **{campo: valor}).status_code == status


@pytest.mark.limites
@pytest.mark.parametrize("motivo, status", [("x" * 300, 200), ("x" * 301, 422)])
def test_motivo_de_pausa_hasta_300_caracteres(client, headers, motivo, status):
    agent_id = registrar(client, headers("admin")).json()["agent"]["id"]
    r = client.post(f"/gov/agents/{agent_id}/pause", json={"reason": motivo}, headers=headers("admin"))
    assert r.status_code == status


@pytest.mark.limites
@pytest.mark.parametrize("nombre, status", [("S", 422), ("Si", 201), ("S" * 80, 201), ("S" * 81, 422)])
def test_nombre_del_sistema_entre_2_y_80_caracteres(client, headers, nombre, status):
    r = client.post("/gov/sistemas", json={"name": nombre, "area_id": "plataforma"}, headers=headers("admin"))
    assert r.status_code == status


@pytest.mark.limites
@pytest.mark.regresion
@pytest.mark.parametrize("limite, status", [(-1, 422), (0, 422), (1, 200)])
def test_limite_de_avisos_minimo_1(client, headers, limite, status):
    """Regresión: un LIMIT negativo provoca un 500 en Postgres (la base real de governance)."""
    assert client.get(f"/gov/notifications?limit={limite}", headers=headers("viewer")).status_code == status


@pytest.mark.limites
def test_limite_de_avisos_se_recorta_a_200(client, headers, db):
    for i in range(201):
        notify(db, "registro", f"Aviso {i}")
    data = client.get("/gov/notifications?limit=500", headers=headers("viewer")).json()
    assert len(data["items"]) == 200 and data["unread"] == 201


@pytest.fixture
def vigilado(client, headers):
    return registrar(client, headers("admin"), "Vigilado", "talentia").json()["agent"]["id"]


@pytest.mark.limites
@pytest.mark.parametrize("gasto, estado, aviso", [
    (0.79, "activo", None),               # justo debajo del umbral de aviso (80 %)
    (0.80, "activo", "aviso_gasto"),      # en el umbral de aviso
    (0.99, "activo", "aviso_gasto"),      # justo debajo del presupuesto
    (1.00, "pausado", "auto_pausa_gasto"),  # en el presupuesto
])
def test_umbrales_de_gasto(gateway, vigilado, gasto, estado, aviso):
    gateway.set_spend(agente(vigilado).key_hash, gasto, 1.0)
    asyncio.run(monitor.run_once())
    assert agente(vigilado).status == estado
    tipos = [n.kind for n in avisos() if n.kind != "registro"]
    assert tipos == ([aviso] if aviso else [])


@pytest.mark.limites
@pytest.mark.parametrize("llamadas, fallidas, estado", [
    (4, 3, "activo"),    # 75 % pero menos llamadas que el mínimo (5)
    (5, 3, "pausado"),   # mínimo de llamadas y 60 % > 50 %
    (10, 5, "activo"),   # exactamente 50 %: no supera el umbral
    (10, 6, "pausado"),  # 60 %
])
def test_umbrales_de_tasa_de_errores(gateway, vigilado, llamadas, fallidas, estado):
    gateway.add_logs(agente(vigilado).key_hash, llamadas, fallidas)
    asyncio.run(monitor.run_once())
    assert agente(vigilado).status == estado


@pytest.mark.particion
@pytest.mark.parametrize("sistema, area", [("talentia", "rrhh"), ("agentfactory", "desarrollo"), ("tokenio", "plataforma")])
def test_particion_por_sistema_el_area_se_hereda(client, headers, sistema, area):
    r = registrar(client, headers("admin"), f"Agente {sistema}", sistema)
    assert r.json()["agent"]["area_id"] == area and r.json()["agent"]["sistema_id"] == sistema_id(sistema)
