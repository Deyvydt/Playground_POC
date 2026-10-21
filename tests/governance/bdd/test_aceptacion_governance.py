"""Escenarios de aceptación de governance (spec 002)."""
from pytest_bdd import scenarios

scenarios("specs/002-llm-gateway/features/registro_agentes.feature")
scenarios("specs/002-llm-gateway/features/presupuestos.feature")
scenarios("specs/002-llm-gateway/features/kill_switch.feature")
