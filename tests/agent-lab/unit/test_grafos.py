import asyncio

import pytest

from app.graphs import agentfactory, talentia


@pytest.mark.parametrize("texto, puntaje", [("85", 85), ("Puntaje: 72/100", 72), ("150", 100), ("sin número", 0)])
def test_parse_puntaje_extrae_el_primer_numero_entre_0_y_100(texto, puntaje):
    assert talentia._parse_puntaje(texto) == puntaje


@pytest.mark.parametrize("estado, ruta", [
    ({"puntaje": 70}, "entrevista"),
    ({"puntaje": 69}, "rechazo"),
    ({"puntaje": 95, "error": "pausado"}, "fin"),
])
def test_ruta_de_talentia_depende_del_puntaje_y_de_errores(estado, ruta):
    assert talentia._ruta_evaluacion(estado) == ruta


@pytest.mark.parametrize("texto, observaciones", [
    ("OBSERVACIONES: ninguna", ""),
    ("observaciones:   Ninguna.", ""),
    ("OBSERVACIONES: falta validar la moneda", "falta validar la moneda"),
    ("El código no compila", "El código no compila"),
])
def test_parse_observaciones(texto, observaciones):
    assert agentfactory._parse_observaciones(texto) == observaciones


@pytest.mark.parametrize("estado, ruta", [
    ({"observaciones": "falta algo", "ronda": 1}, "corregir"),
    ({"observaciones": "falta algo", "ronda": agentfactory.MAX_RONDAS}, "tests"),
    ({"observaciones": "", "ronda": 1}, "tests"),
    ({"observaciones": "x", "ronda": 1, "error": "pausado"}, "fin"),
])
def test_ruta_de_revision_limita_las_rondas_de_correccion(estado, ruta):
    assert agentfactory._ruta_revision(estado) == ruta


def _run(grafo, **estado):
    return asyncio.run(grafo.build_graph().ainvoke({"run_id": "run-1", "trace": [], **estado}))


def test_agentfactory_sin_aprobacion_del_revisor_se_detiene_tras_el_maximo_de_rondas(model):
    resultado = _run(agentfactory, requerimiento="endpoint", ronda=0, observaciones="")
    assert model.path.count("generador_codigo") == agentfactory.MAX_RONDAS
    assert model.path[-2:] == ["generador_tests", "documentador"]
    assert resultado["documentacion"] == "Salida simulada de documentador"


def test_el_codigo_corregido_recibe_las_observaciones_del_revisor(model):
    model.respond("revisor_codigo", "OBSERVACIONES: usar BigDecimal", "OBSERVACIONES: ninguna")
    _run(agentfactory, requerimiento="endpoint", ronda=0, observaciones="")
    segunda_generacion = [c for c in model.calls if c["nodo"] == "generador_codigo"][1]
    assert "usar BigDecimal" in segunda_generacion["messages"][1]["content"]


def test_un_error_en_un_nodo_corta_el_grafo_y_queda_en_la_traza(model):
    model.fail("analizador_cv", 401)
    resultado = _run(talentia, cv="cv", vacante="vacante")
    assert model.path == ["analizador_cv"]
    assert resultado["error"] == "El agente está pausado por un administrador."
    assert resultado["trace"][-1]["estado"] == "error"
