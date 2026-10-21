"""Valores límite de los grafos de agent-lab."""
import asyncio

import pytest

from app.graphs import agentfactory, talentia


@pytest.mark.limites
@pytest.mark.parametrize("respuesta, puntaje, ruta", [
    ("0", 0, "rechazo"), ("69", 69, "rechazo"), ("70", 70, "entrevista"), ("100", 100, "entrevista"), ("101", 100, "entrevista"),
])
def test_puntaje_en_los_limites_de_la_escala_y_del_corte(respuesta, puntaje, ruta):
    valor = talentia._parse_puntaje(respuesta)
    assert valor == puntaje
    assert talentia._ruta_evaluacion({"puntaje": valor}) == ruta


@pytest.mark.limites
@pytest.mark.parametrize("rondas_con_observaciones, generaciones", [(0, 1), (1, 2), (2, 2), (5, 2)])
def test_rondas_de_correccion_nunca_superan_el_maximo(model, rondas_con_observaciones, generaciones):
    respuestas = ["OBSERVACIONES: corregir"] * rondas_con_observaciones + ["OBSERVACIONES: ninguna"] * 3
    model.respond("revisor_codigo", *respuestas)
    asyncio.run(agentfactory.build_graph().ainvoke(
        {"run_id": "r", "requerimiento": "x", "ronda": 0, "observaciones": "", "trace": []}))
    assert model.path.count("generador_codigo") == generaciones
    assert model.path[-2:] == ["generador_tests", "documentador"]
