import asyncio

import pytest
from sqlmodel import Session, select

from app import llm, secrets
from app.database import engine
from app.models import AgentCredential
from fakes import gateway_error


@pytest.mark.particion
@pytest.mark.parametrize("status, mensaje", [
    (401, "El agente está pausado por un administrador."),
    (400, "El agente agotó su presupuesto o límite de uso."),
    (429, "El agente agotó su presupuesto o límite de uso."),
    (403, "El agente agotó su presupuesto o límite de uso."),
    (0, "El gateway no está disponible."),
    (500, "El gateway rechazó la llamada (500)."),
])
def test_errores_del_gateway_se_traducen_a_mensajes_claros(status, mensaje):
    assert llm._mensaje_error(gateway_error(status)) == mensaje


def test_call_node_usa_la_key_del_nodo_y_envia_la_traza(model):
    texto, paso = asyncio.run(llm.call_node("talentia", "evaluador_ajuste", "sistema", "entrada", "run-42"))
    llamada = model.calls[0]
    assert llamada["api_key"] == "sk-evaluador_ajuste" and llamada["model"] == "llama-local"
    assert llamada["base_url"] == "http://gateway.invalid:9/v1"
    assert llamada["metadata"] == {
        "agent_id": 2, "sistema": "talentia", "area": "rrhh", "run_id": "run-42", "trace_id": "run-42",
        "trace_name": "talentia · grafo", "generation_name": "evaluador_ajuste",
        "tags": ["agent:2", "area:rrhh", "sistema:talentia"],
    }
    assert paso == {"nodo": "evaluador_ajuste", "estado": "ok", "entrada": "entrada", "salida": texto,
                    "tokens_entrada": 11, "tokens_salida": 7}


@pytest.mark.limites
def test_call_node_recorta_entrada_y_salida_en_la_traza(model):
    model.respond("analizador_cv", "x" * 900)
    _, paso = asyncio.run(llm.call_node("talentia", "analizador_cv", "s", "e" * 900, "r"))
    assert (len(paso["entrada"]), len(paso["salida"])) == (300, 500)


def test_las_keys_se_guardan_cifradas_y_se_recuperan_en_claro():
    with Session(engine) as session:
        cred = session.exec(select(AgentCredential).where(AgentCredential.nodo == "documentador")).one()
    assert "sk-documentador" not in cred.key_enc
    assert secrets.get_credential("agentfactory", "documentador") == (8, "sk-documentador")


def test_guardar_de_nuevo_reemplaza_la_key_del_nodo():
    secrets.save("talentia", "analizador_cv", 99, "talentia/analizador_cv", "sk-nueva")
    assert secrets.get_credential("talentia", "analizador_cv") == (99, "sk-nueva")


def test_nodo_sin_credencial_pide_ejecutar_provision():
    with pytest.raises(RuntimeError, match="provision.py"):
        secrets.get_credential("talentia", "inexistente")
    assert secrets.exists("talentia", "analizador_cv") and not secrets.exists("talentia", "inexistente")
