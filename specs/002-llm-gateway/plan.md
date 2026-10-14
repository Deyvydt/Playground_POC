# Plan Técnico: Gobierno de LLMs

Ver `spec.md` para el alcance funcional.

## Arquitectura (microservicios)

```
frontend React :5173   /api → backend   /gov → governance   /lab → agent-lab

backend TokenIO :8000 (6 agentes) ─┐
agent-lab :8200 (LangGraph)  ──────┤  virtual key por agente · API formato OpenAI
agentes externos (red local) ──────┘
                                   ▼
                gateway LiteLLM Proxy :4000 ── Postgres (pgserver) db "litellm"
                   │ alias llama-local / embed-local · costo interno · budgets · rpm/tpm
                   │ webhook de alertas ──► governance
                   │ trazas sin contenido ──► Langfuse Cloud
                   ▼
                Ollama :11434 (solo el gateway lo llama)

governance :8100 ── db "governance"
   registro de áreas/sistemas/agentes · kill switch · monitor de auto-pausa ·
   notificaciones · consulta de gasto vía admin API de LiteLLM
```

## Decisiones técnicas

| Tema | Decisión | Razón |
|---|---|---|
| Gateway | LiteLLM Proxy (open source) | Virtual keys, teams, budgets, rate limits, alias, balanceo y alertas ya resueltos. |
| BD del gateway | Postgres vía `pgserver` (pip) | LiteLLM exige Postgres para keys/budgets; pgserver no requiere admin ni Docker. |
| Organización | Vive en governance | Organizations es función enterprise de LiteLLM; Teams + Keys son open source. |
| Costo de modelos locales | `model_info.input/output_cost_per_token` > 0 | Con costo 0 LiteLLM omite el chequeo de presupuesto. |
| Agentes de prueba | LangGraph + `ChatOpenAI(base_url=gateway)` | Framework de grafos con ramas y bucles; el cliente OpenAI es lo que usará cualquier sistema externo. |
| Trazas | Langfuse Cloud, `turn_off_message_logging` | Rápido de probar sin Docker y sin sacar el texto de los prompts de la red. |
| Secretos de clientes | Key cifrada (Fernet) en la BD de cada cliente | El registro solo guarda alias + hash; la key en claro solo la tiene quien la consume. |
| Auth de governance | Token de sesión de TokenIO verificado con `SECRET_KEY` compartido | Un solo login; mismos roles (`admin`, `developer`, `viewer`). |

## Preparación para la Opción 1

- `Agente.runtime` = `external` | `hosted`.
- agent-lab ya es un runtime de agentes alojados detrás de una API: exponerlo a
  clientes es agregar autenticación por cliente, no rediseñar.

## Fases

0. Specs (este documento) y `.gitignore`.
1. Gateway mínimo: pgserver + LiteLLM + alias locales + 1 virtual key.
2. Teams, access groups, presupuestos, límites + `verify_gateway.py`.
3. Microservicio governance: registro, kill switch, auto-pausa, notificaciones.
4. Microservicio agent-lab: grafos Talentia y AgentFactory.
5. Backend de TokenIO consume vía gateway (`ollama_client.py` como adaptador).
6. Langfuse Cloud.
7. UI: Gobierno, Registro de agentes, Notificaciones, Laboratorio.
8. Modo servidor en red local, README y `docker-compose.yml`.
