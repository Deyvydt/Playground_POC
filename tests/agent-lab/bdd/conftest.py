"""Pasos Gherkin de agent-lab (spec 002, US-6)."""
import pytest
from pytest_bdd import given, parsers, then, when

USER = {"Authorization": "Bearer rol:developer"}
ENTRADAS = {
    "talentia": {"cv": "Ana Torres, 6 años en Java y Quarkus.", "vacante": "Desarrollador Java Senior."},
    "agentfactory": {"requerimiento": "Endpoint REST que convierta montos entre PEN y USD."},
}


@pytest.fixture
def ctx():
    return {}


@given(parsers.parse('que el nodo "{nodo}" responderá "{primera}" y luego "{segunda}"'))
def nodo_responde_dos(model, nodo, primera, segunda):
    model.respond(nodo, primera, segunda)


@given(parsers.parse('que el nodo "{nodo}" responderá "{salida}"'))
def nodo_responde(model, nodo, salida):
    model.respond(nodo, salida)


@given(parsers.parse('que el nodo "{nodo}" está pausado en el gateway'))
def nodo_pausado(model, nodo):
    model.fail(nodo, 401)


@when(parsers.parse('ejecuto el grafo "{sistema}" con un CV y una vacante'))
@when(parsers.parse('ejecuto el grafo "{sistema}" con un requerimiento'))
def ejecutar(client, ctx, sistema):
    ctx["response"] = client.post(f"/lab/runs/{sistema}", json=ENTRADAS[sistema], headers=USER)
    assert ctx["response"].status_code == 200, ctx["response"].text


@then(parsers.parse('el recorrido fue "{nodos}"'))
def recorrido(ctx, nodos):
    assert [p["nodo"] for p in ctx["response"].json()["trace"]] == [n.strip() for n in nodos.split(",")]


@then(parsers.parse("el resultado incluye el puntaje {puntaje:d}"))
def puntaje(ctx, puntaje):
    assert ctx["response"].json()["resultado"]["puntaje"] == puntaje


@then("cada nodo usó una virtual key distinta")
def keys_distintas(model):
    keys = [c["api_key"] for c in model.calls]
    assert len(keys) == len(set(keys)) and all(k.startswith("sk-") for k in keys)


@then("cada llamada llevó el identificador de la ejecución como traza")
def traza_por_ejecucion(ctx, model):
    run_id = ctx["response"].json()["run_id"]
    assert {c["metadata"]["trace_id"] for c in model.calls} == {run_id}


@then(parsers.parse('el grafo se detuvo con el mensaje "{mensaje}"'))
def detenido(ctx, mensaje):
    body = ctx["response"].json()
    assert body["error"] == mensaje and body["trace"][-1]["mensaje"] == mensaje
