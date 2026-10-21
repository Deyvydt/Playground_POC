"""Grafo 'Fábrica Quarkus' de AgentFactory (Desarrollo): un nodo = un agente = una virtual key."""
import operator
import re
from typing import Annotated, TypedDict
from langgraph.graph import END, START, StateGraph
from app.llm import call_node

SISTEMA = "agentfactory"
MAX_RONDAS = 2


class AgentFactoryState(TypedDict):
    run_id: str
    requerimiento: str
    codigo: str
    tests: str
    documentacion: str
    observaciones: str
    ronda: int
    error: str | None
    trace: Annotated[list[dict], operator.add]


def _parse_observaciones(texto: str) -> str:
    match = re.search(r"OBSERVACIONES:\s*(.*)", texto, re.IGNORECASE | re.DOTALL)
    contenido = (match.group(1).strip() if match else texto.strip())
    return "" if contenido.lower().startswith("ninguna") else contenido


async def generador_codigo(state: AgentFactoryState) -> dict:
    if state.get("error"):
        return {}
    prompt = (
        "Eres un generador de código Java/Quarkus. Genera un recurso REST y una entidad Panache que cumplan "
        "el requerimiento. Responde solo con el código."
    )
    if state.get("observaciones"):
        entrada = (
            f"Requerimiento:\n{state['requerimiento']}\n\nCódigo anterior:\n{state['codigo']}\n\n"
            f"Observaciones a corregir:\n{state['observaciones']}"
        )
    else:
        entrada = f"Requerimiento:\n{state['requerimiento']}"
    texto, paso = await call_node(SISTEMA, "generador_codigo", prompt, entrada, state["run_id"])
    if paso["estado"] == "error":
        return {"error": paso["mensaje"], "trace": [paso]}
    return {"codigo": texto, "trace": [paso]}


async def revisor_codigo(state: AgentFactoryState) -> dict:
    if state.get("error"):
        return {}
    prompt = (
        "Eres un revisor de código Java/Quarkus. Revisa el código frente al requerimiento y responde EXACTAMENTE "
        "en este formato:\nOBSERVACIONES: ninguna\n(si no hay problemas) o\nOBSERVACIONES: <lista de problemas>"
    )
    entrada = f"Requerimiento:\n{state['requerimiento']}\n\nCódigo:\n{state['codigo']}"
    texto, paso = await call_node(SISTEMA, "revisor_codigo", prompt, entrada, state["run_id"])
    if paso["estado"] == "error":
        return {"error": paso["mensaje"], "trace": [paso]}
    return {"observaciones": _parse_observaciones(texto), "ronda": state.get("ronda", 0) + 1, "trace": [paso]}


async def generador_tests(state: AgentFactoryState) -> dict:
    if state.get("error"):
        return {}
    prompt = (
        "Eres un generador de tests Java. Genera tests JUnit 5 con RestAssured para el código dado. "
        "Responde solo con el código de los tests."
    )
    entrada = f"Requerimiento:\n{state['requerimiento']}\n\nCódigo:\n{state['codigo']}"
    texto, paso = await call_node(SISTEMA, "generador_tests", prompt, entrada, state["run_id"])
    if paso["estado"] == "error":
        return {"error": paso["mensaje"], "trace": [paso]}
    return {"tests": texto, "trace": [paso]}


async def documentador(state: AgentFactoryState) -> dict:
    if state.get("error"):
        return {}
    prompt = (
        "Eres un documentador técnico. Escribe, en español, una documentación breve (endpoints, modelo de datos "
        "y cómo probarlo) para el código y los tests generados."
    )
    entrada = f"Requerimiento:\n{state['requerimiento']}\n\nCódigo:\n{state['codigo']}\n\nTests:\n{state['tests']}"
    texto, paso = await call_node(SISTEMA, "documentador", prompt, entrada, state["run_id"])
    if paso["estado"] == "error":
        return {"error": paso["mensaje"], "trace": [paso]}
    return {"documentacion": texto, "trace": [paso]}


def _ruta_revision(state: AgentFactoryState) -> str:
    if state.get("error"):
        return "fin"
    if state.get("observaciones") and state.get("ronda", 0) < MAX_RONDAS:
        return "corregir"
    return "tests"


def build_graph():
    g = StateGraph(AgentFactoryState)
    g.add_node("generador_codigo", generador_codigo)
    g.add_node("revisor_codigo", revisor_codigo)
    g.add_node("generador_tests", generador_tests)
    g.add_node("documentador", documentador)
    g.add_edge(START, "generador_codigo")
    g.add_edge("generador_codigo", "revisor_codigo")
    g.add_conditional_edges(
        "revisor_codigo",
        _ruta_revision,
        {"corregir": "generador_codigo", "tests": "generador_tests", "fin": END},
    )
    g.add_edge("generador_tests", "documentador")
    g.add_edge("documentador", END)
    return g.compile()
