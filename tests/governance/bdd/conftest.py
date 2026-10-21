"""Pasos Gherkin de governance (spec 002: US-2, US-3 y US-4)."""
import asyncio

import pytest
from pytest_bdd import given, parsers, then, when
from sqlmodel import Session

from app import monitor
from app.database import engine
from app.models import Agente
from support import agente, avisos, registrar

ADMIN = {"Authorization": "Bearer rol:admin"}


@pytest.fixture
def ctx():
    return {"headers": ADMIN}


def _registrar(client, ctx, headers, nombre, sistema, **extra):
    ctx["response"] = registrar(client, headers, nombre, sistema, **extra)
    if ctx["response"].status_code == 201:
        body = ctx["response"].json()
        ctx["agent_id"] = body["agent"]["id"]
        ctx["key"] = body["connection"]["api_key"]
    return ctx["response"]


def _key_hash(ctx):
    return agente(ctx["agent_id"]).key_hash


# --- Dado ---------------------------------------------------------------------------------

@given(parsers.parse('que soy un usuario de governance con rol "{rol}"'))
def usuario(ctx, rol):
    ctx["headers"] = {"Authorization": f"Bearer rol:{rol}"}


@given(parsers.parse('que registré el agente "{nombre}" en el sistema "{sistema}"'))
def ya_registrado(client, ctx, nombre, sistema):
    assert _registrar(client, ctx, ADMIN, nombre, sistema).status_code == 201


@given(parsers.parse('que el gateway reporta para el team "{team}" un gasto de {gasto:g} de {presupuesto:g}'))
def gasto_team(gateway, team, gasto, presupuesto):
    gateway.teams[team] = {"spend": gasto, "max_budget": presupuesto}


@given(parsers.parse("que el gateway reporta para el agente un gasto de {gasto:g} de {presupuesto:g}"))
def gasto_agente(gateway, ctx, gasto, presupuesto):
    gateway.set_spend(_key_hash(ctx), gasto, presupuesto)


@given(parsers.parse("que el gateway reporta para el agente {total:d} llamadas recientes con {fallidas:d} fallidas"))
def llamadas_recientes(gateway, ctx, total, fallidas):
    gateway.add_logs(_key_hash(ctx), total, fallidas)


# --- Cuando -------------------------------------------------------------------------------

@when(parsers.parse('registro el agente "{nombre}" en el sistema "{sistema}"'))
def registrar_agente(client, ctx, nombre, sistema):
    _registrar(client, ctx, ctx["headers"], nombre, sistema)


@when(parsers.parse('registro el agente "{nombre}" en el sistema "{sistema}" con presupuesto {presupuesto:g} por '
                    '"{periodo}", {rpm:d} solicitudes y {tpm:d} tokens por minuto'))
def registrar_con_limites(client, ctx, nombre, sistema, presupuesto, periodo, rpm, tpm):
    _registrar(client, ctx, ctx["headers"], nombre, sistema,
               max_budget=presupuesto, budget_duration=periodo, rpm_limit=rpm, tpm_limit=tpm)


@when("regenero su key")
def regenerar(client, ctx):
    ctx["key_anterior"] = ctx["key"]
    ctx["response"] = client.post(f"/gov/agents/{ctx['agent_id']}/regenerate-key", headers=ctx["headers"])
    ctx["key"] = ctx["response"].json()["connection"]["api_key"]


@when(parsers.parse("cambio su presupuesto a {presupuesto:g}"))
def cambiar_presupuesto(client, ctx, presupuesto):
    ctx["response"] = client.patch(f"/gov/agents/{ctx['agent_id']}", json={"max_budget": presupuesto}, headers=ctx["headers"])


@when("consulto las áreas")
def consultar_areas(client, ctx):
    ctx["response"] = client.get("/gov/areas", headers=ctx["headers"])


@when(parsers.parse('pauso el agente con el motivo "{motivo}"'))
def pausar(client, ctx, motivo):
    ctx["response"] = client.post(f"/gov/agents/{ctx['agent_id']}/pause", json={"reason": motivo}, headers=ctx["headers"])


@when("reactivo el agente")
def reactivar(client, ctx):
    ctx["response"] = client.post(f"/gov/agents/{ctx['agent_id']}/resume", headers=ctx["headers"])


@when("corre el monitor")
def correr_monitor():
    asyncio.run(monitor.run_once())


@when(parsers.parse('el gateway envía el aviso "{evento}" para la key del agente'))
def aviso_gateway(client, ctx, evento):
    ctx["response"] = client.post("/gov/alerts/gateway?token=token-webhook-pruebas",
                                  json={"event": evento, "token": _key_hash(ctx), "spend": 1.1, "max_budget": 1.0})


@when("alguien envía un aviso al webhook con un token inválido")
def aviso_falso(client, ctx):
    ctx["response"] = client.post("/gov/alerts/gateway?token=falso", json={"event": "budget_crossed"})


# --- Entonces -----------------------------------------------------------------------------

@then(parsers.parse("la respuesta tiene el código {codigo:d}"))
def codigo(ctx, codigo):
    assert ctx["response"].status_code == codigo, ctx["response"].text


@then(parsers.parse('recibo una virtual key que empieza por "{prefijo}"'))
def key_recibida(ctx, prefijo):
    assert ctx["key"].startswith(prefijo)


@then(parsers.parse('la guía de conexión incluye ejemplos para "{lenguajes}"'))
def guia(ctx, lenguajes):
    conexion = ctx["response"].json()["connection"]
    for lenguaje in lenguajes.split(","):
        assert conexion[lenguaje.strip()]


@then("al consultar el agente no aparece la key")
def key_oculta(client, ctx):
    assert ctx["key"] not in client.get(f"/gov/agents/{ctx['agent_id']}", headers=ADMIN).text


@then(parsers.parse('el registro guardado tiene el alias "{alias}"'))
def alias_guardado(ctx, alias):
    assert agente(ctx["agent_id"]).key_alias == alias


@then("el registro guardado no contiene la key en claro")
def sin_key_en_claro(ctx, gateway):
    guardado = agente(ctx["agent_id"]).model_dump()
    assert ctx["key"] not in str(guardado)
    assert guardado["key_hash"] == gateway.hash_of(ctx["key"])


@then("recibo una virtual key distinta a la anterior")
def key_distinta(ctx):
    assert ctx["key"] != ctx["key_anterior"]


@then("la key anterior ya no existe en el gateway")
def key_anterior_borrada(ctx, gateway):
    assert gateway.hash_of(ctx["key_anterior"]) not in gateway.keys
    assert gateway.hash_of(ctx["key"]) in gateway.keys


@then(parsers.parse('el agente queda en el área "{area}" y en el sistema "{sistema}"'))
def jerarquia(ctx, area, sistema):
    data = ctx["response"].json()["agent"]
    assert (data["area"]["id"], data["sistema"]["slug"]) == (area, sistema)


@then(parsers.parse('su key se emite para el team "{team}" del gateway'))
def team_de_la_key(ctx, gateway, team):
    assert gateway.keys[_key_hash(ctx)]["fields"]["team_id"] == team


@then(parsers.parse('el gateway recibió para su key el presupuesto {presupuesto:g}, el periodo "{periodo}", '
                    '{rpm:d} solicitudes y {tpm:d} tokens por minuto'))
def limites_en_gateway(ctx, gateway, presupuesto, periodo, rpm, tpm):
    campos = gateway.keys[_key_hash(ctx)]["fields"]
    assert (campos["max_budget"], campos["budget_duration"], campos["rpm_limit"], campos["tpm_limit"]) == (presupuesto, periodo, rpm, tpm)


@then(parsers.parse("el gateway recibió para su key el presupuesto {presupuesto:g}"))
def presupuesto_en_gateway(ctx, gateway, presupuesto):
    assert gateway.keys[_key_hash(ctx)]["fields"]["max_budget"] == presupuesto


@then(parsers.parse('el gateway recibió los modelos "{modelos}"'))
def modelos_en_gateway(ctx, gateway, modelos):
    assert gateway.keys[_key_hash(ctx)]["fields"]["models"] == [m.strip() for m in modelos.split(",")]


@then(parsers.parse('el área "{area}" muestra un uso del {porcentaje:d}%'))
def uso_area(ctx, area, porcentaje):
    fila = next(a for a in ctx["response"].json() if a["id"] == area)
    assert round(fila["usage"]["budget_ratio"] * 100) == porcentaje


@then(parsers.parse('el agente queda "{estado}" con el motivo "{motivo}"'))
def estado_con_motivo(ctx, estado, motivo):
    a = agente(ctx["agent_id"])
    assert (a.status, a.pause_reason) == (estado, motivo)


@then(parsers.parse('el agente queda "{estado}"'))
def estado(ctx, estado):
    assert agente(ctx["agent_id"]).status == estado


@then("su key está bloqueada en el gateway")
def bloqueada(ctx, gateway):
    assert gateway.keys[_key_hash(ctx)]["blocked"] is True


@then("su key no está bloqueada en el gateway")
def no_bloqueada(ctx, gateway):
    assert gateway.keys[_key_hash(ctx)]["blocked"] is False


@then(parsers.parse('hay un aviso "{tipo}" de severidad "{severidad}"'))
def aviso(tipo, severidad):
    assert [n.severity for n in avisos(tipo)] == [severidad]


@then(parsers.parse('hay exactamente {cantidad:d} aviso "{tipo}"'))
def cantidad_avisos(cantidad, tipo):
    assert len(avisos(tipo)) == cantidad
