import asyncio

import pytest
from sqlmodel import select

from app import litellm_admin, registry
from app.models import Agente, Notification
from support import sistema_id


def nuevo(db, nombre="Agente Unitario", sistema="talentia", **campos):
    a = Agente(name=nombre, sistema_id=sistema_id(sistema), area_id="", slug="", key_alias="", key_hash="",
               models=["local-models"], max_budget=1.0, budget_duration="30d", **campos)
    key = asyncio.run(registry.register(db, a, "Ana"))
    return a, key


@pytest.mark.particion
@pytest.mark.adivinanza_errores
@pytest.mark.parametrize("texto, slug", [
    ("Asistente de RR.HH.", "asistente-de-rr-hh"),
    ("  Análisis   Ñandú ", "analisis-nandu"),
    ("!!!", "agente"),
])
def test_slugify_genera_identificadores_legibles(texto, slug):
    assert registry.slugify(texto) == slug


def test_registrar_hereda_el_area_del_sistema_y_guarda_solo_el_hash(db, gateway):
    a, key = nuevo(db)
    assert (a.area_id, a.key_alias) == ("rrhh", "talentia/agente-unitario")
    assert a.key_hash == gateway.hash_of(key) and key not in a.key_hash
    enviado = gateway.keys[a.key_hash]["fields"]
    assert enviado["team_id"] == "rrhh" and enviado["metadata"]["sistema"] == "talentia"


@pytest.mark.particion
def test_registrar_un_nombre_repetido_en_el_mismo_sistema_falla(db):
    nuevo(db)
    with pytest.raises(ValueError, match="Ya existe"):
        nuevo(db)


@pytest.mark.adivinanza_errores
def test_si_el_gateway_falla_el_agente_no_queda_registrado(db, gateway):
    gateway.down = True
    with pytest.raises(litellm_admin.GatewayError):
        nuevo(db)
    assert db.exec(select(Agente)).all() == []


@pytest.mark.transicion_estados
def test_regenerar_la_key_de_un_agente_pausado_la_deja_bloqueada(db, gateway):
    a, key = nuevo(db)
    asyncio.run(registry.pause(db, a, "motivo", "Ana"))
    nueva = asyncio.run(registry.regenerate_key(db, a, "Ana"))
    assert nueva != key and gateway.hash_of(key) not in gateway.keys
    assert gateway.keys[a.key_hash]["blocked"] is True


@pytest.mark.transicion_estados
def test_pausar_dos_veces_no_duplica_el_aviso(db):
    a, _ = nuevo(db)
    asyncio.run(registry.pause(db, a, "uno", "Ana"))
    asyncio.run(registry.pause(db, a, "dos", "Ana"))
    assert a.pause_reason == "uno"
    assert len(db.exec(select(Notification).where(Notification.kind == "pausa_manual")).all()) == 1


def test_la_pausa_automatica_es_critica_y_la_manual_es_advertencia(db):
    a, _ = nuevo(db, "Uno")
    b, _ = nuevo(db, "Dos")
    asyncio.run(registry.pause(db, a, "manual", "Ana"))
    asyncio.run(registry.pause(db, b, "gasto", registry.AUTO, kind="auto_pausa_gasto"))
    severidades = {n.kind: n.severity for n in db.exec(select(Notification)).all()}
    assert severidades["pausa_manual"] == "warning" and severidades["auto_pausa_gasto"] == "critical"


def test_actualizar_limites_reinicia_el_aviso_de_gasto(db, gateway):
    a, _ = nuevo(db)
    a.budget_warning_sent = True
    asyncio.run(registry.update_limits(db, a, {"max_budget": 9.0, "rpm_limit": 5}))
    assert a.budget_warning_sent is False
    assert gateway.keys[a.key_hash]["fields"]["max_budget"] == 9.0
    assert gateway.keys[a.key_hash]["fields"]["rpm_limit"] == 5


def test_dar_de_baja_conserva_el_historial_de_avisos(db, gateway):
    a, _ = nuevo(db)
    hash_ = a.key_hash
    asyncio.run(registry.deregister(db, a, "Ana"))
    assert hash_ not in gateway.keys
    kinds = [n.kind for n in db.exec(select(Notification)).all()]
    assert kinds == ["registro", "baja"]
    assert all(n.agente_id is None for n in db.exec(select(Notification)).all())


def test_uso_sin_gateway_se_informa_como_no_disponible(db, gateway):
    a, _ = nuevo(db)
    gateway.down = True
    assert asyncio.run(registry.usage(a)) == {"available": False}


def test_guia_de_conexion_usa_la_url_publica_y_la_key(db):
    a, key = nuevo(db)
    guia = registry.connection_guide(a, key)
    assert guia["base_url"] == "http://192.168.1.50:4000/v1" and guia["api_key"] == key
    assert "quarkus.langchain4j.openai.base-url=http://192.168.1.50:4000/v1" in guia["java"]
    assert key not in guia["python"]  # los ejemplos usan un marcador, no la key real
