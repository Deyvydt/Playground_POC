"""Escenarios de aceptación del backend: cada .feature de la spec 001 y la US-7 de la spec 002."""
from pytest_bdd import scenarios

scenarios("specs/001-agent-playground/features")
scenarios("specs/002-llm-gateway/features/agentes_tokenio.feature")
