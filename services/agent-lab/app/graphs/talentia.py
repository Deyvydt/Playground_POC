"""Grafo 'Proceso de selección' de Talentia (RR.HH.): un nodo = un agente = una virtual key."""
import operator
import re
from typing import Annotated, TypedDict
from langgraph.graph import END, START, StateGraph
from app.llm import call_node

SISTEMA = "talentia"


class TalentiaState(TypedDict):
    run_id: str
    cv: str
    vacante: str
    analisis_cv: str
    puntaje: int
    resultado: str
    error: str | None
    trace: Annotated[list[dict], operator.add]


def _parse_puntaje(texto: str) -> int:
    match = re.search(r"\d+", texto)
    return max(0, min(100, int(match.group()))) if match else 0


async def analizador_cv(state: TalentiaState) -> dict:
    prompt = (
        "Eres un analista de selección de RR.HH. Analiza el CV de un candidato frente a una vacante. "
        "Resume en español, en pocas líneas, habilidades, experiencia y formación relevantes para la vacante."
    )
    entrada = f"Vacante:\n{state['vacante']}\n\nCV:\n{state['cv']}"
    texto, paso = await call_node(SISTEMA, "analizador_cv", prompt, entrada, state["run_id"])
    if paso["estado"] == "error":
        return {"error": paso["mensaje"], "trace": [paso]}
    return {"analisis_cv": texto, "trace": [paso]}


async def evaluador_ajuste(state: TalentiaState) -> dict:
    if state.get("error"):
        return {}
    prompt = (
        "Eres un evaluador de ajuste candidato-vacante. Responde SOLO con un número entero de 0 a 100 "
        "que indique qué tan bien encaja el candidato en la vacante. Sin texto adicional."
    )
    entrada = f"Vacante:\n{state['vacante']}\n\nAnálisis del candidato:\n{state['analisis_cv']}"
    texto, paso = await call_node(SISTEMA, "evaluador_ajuste", prompt, entrada, state["run_id"])
    if paso["estado"] == "error":
        return {"error": paso["mensaje"], "trace": [paso]}
    return {"puntaje": _parse_puntaje(texto), "trace": [paso]}


async def generador_entrevista(state: TalentiaState) -> dict:
    if state.get("error"):
        return {}
    prompt = (
        "Eres un entrevistador técnico. Genera, en español, 5 preguntas de entrevista para el candidato "
        "según su análisis y la vacante."
    )
    entrada = f"Vacante:\n{state['vacante']}\n\nAnálisis del candidato:\n{state['analisis_cv']}\n\nPuntaje de ajuste: {state['puntaje']}"
    texto, paso = await call_node(SISTEMA, "generador_entrevista", prompt, entrada, state["run_id"])
    if paso["estado"] == "error":
        return {"error": paso["mensaje"], "trace": [paso]}
    return {"resultado": texto, "trace": [paso]}


async def redactor_comunicaciones(state: TalentiaState) -> dict:
    if state.get("error"):
        return {}
    prompt = (
        "Eres un redactor de comunicaciones de RR.HH. Escribe, en español, un mensaje breve y amable de "
        "rechazo para un candidato que no avanza en el proceso, sin dar detalles del puntaje."
    )
    entrada = f"Vacante:\n{state['vacante']}\n\nAnálisis del candidato:\n{state['analisis_cv']}"
    texto, paso = await call_node(SISTEMA, "redactor_comunicaciones", prompt, entrada, state["run_id"])
    if paso["estado"] == "error":
        return {"error": paso["mensaje"], "trace": [paso]}
    return {"resultado": texto, "trace": [paso]}


def _ruta_evaluacion(state: TalentiaState) -> str:
    if state.get("error"):
        return "fin"
    return "entrevista" if state.get("puntaje", 0) >= 70 else "rechazo"


def build_graph():
    g = StateGraph(TalentiaState)
    g.add_node("analizador_cv", analizador_cv)
    g.add_node("evaluador_ajuste", evaluador_ajuste)
    g.add_node("generador_entrevista", generador_entrevista)
    g.add_node("redactor_comunicaciones", redactor_comunicaciones)
    g.add_edge(START, "analizador_cv")
    g.add_edge("analizador_cv", "evaluador_ajuste")
    g.add_conditional_edges(
        "evaluador_ajuste",
        _ruta_evaluacion,
        {"entrevista": "generador_entrevista", "rechazo": "redactor_comunicaciones", "fin": END},
    )
    g.add_edge("generador_entrevista", END)
    g.add_edge("redactor_comunicaciones", END)
    return g.compile()
