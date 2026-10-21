import asyncio

import pytest
from sqlmodel import select

from app import monitor, registry
from app.models import Agente, Notification
from support import sistema_id


@pytest.fixture
def vigilado(db):
    a = Agente(name="Vigilado", sistema_id=sistema_id("talentia"), area_id="", slug="", key_alias="", key_hash="",
               models=["local-models"], max_budget=1.0, budget_duration="30d")
    asyncio.run(registry.register(db, a, "Ana"))
    return a


def kinds(db):
    return [n.kind for n in db.exec(select(Notification).where(Notification.kind != "registro")).all()]


def test_gasto_al_100_por_ciento_pausa_al_agente(db, gateway, vigilado):
    gateway.set_spend(vigilado.key_hash, 1.0)
    asyncio.run(monitor.check_agent(db, vigilado))
    assert vigilado.status == "pausado" and vigilado.paused_by == registry.AUTO
    assert gateway.keys[vigilado.key_hash]["blocked"] is True
    assert kinds(db) == ["auto_pausa_gasto"]


def test_gasto_al_80_por_ciento_avisa_una_sola_vez(db, gateway, vigilado):
    gateway.set_spend(vigilado.key_hash, 0.8)
    asyncio.run(monitor.check_agent(db, vigilado))
    asyncio.run(monitor.check_agent(db, vigilado))
    assert vigilado.status == "activo"
    assert kinds(db) == ["aviso_gasto"]


def test_gasto_bajo_no_genera_avisos(db, gateway, vigilado):
    gateway.set_spend(vigilado.key_hash, 0.5)
    asyncio.run(monitor.check_agent(db, vigilado))
    assert kinds(db) == []


@pytest.mark.parametrize("total, fallidas, pausado", [
    (6, 4, True),    # 67 % > 50 %
    (6, 3, False),   # 50 % no supera el umbral
    (4, 4, False),   # menos llamadas que el mínimo (5)
])
def test_tasa_de_errores(db, gateway, vigilado, total, fallidas, pausado):
    gateway.add_logs(vigilado.key_hash, total, fallidas)
    asyncio.run(monitor.check_agent(db, vigilado))
    assert (vigilado.status == "pausado") is pausado
    assert (kinds(db) == ["auto_pausa_errores"]) is pausado


def test_sin_gateway_el_monitor_no_falla_ni_pausa(db, gateway, vigilado):
    gateway.down = True
    asyncio.run(monitor.run_once())
    gateway.down = False
    assert db.get(Agente, vigilado.id).status == "activo"


def test_run_once_solo_revisa_agentes_activos(db, gateway, vigilado):
    asyncio.run(registry.pause(db, vigilado, "manual", "Ana"))
    gateway.set_spend(vigilado.key_hash, 5.0)
    asyncio.run(monitor.run_once())
    assert kinds(db) == ["pausa_manual"]
