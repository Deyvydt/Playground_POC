# Tareas — Gobierno de LLMs

Generado a partir de `plan.md`.

## Fase 0 — Specs
- [X] T001 `spec.md`, `plan.md`, `tasks.md`
- [X] T002 Enmienda de la constitución (microservicios, gateway, LangGraph)
- [X] T003 `.gitignore` para `services/**/.env` y datos de pgserver

## Fase 1 — Gateway mínimo
- [X] T010 `services/gateway/start_db.py` (pgserver, bases `litellm` y `governance`)
- [X] T011 `config.yaml` con `llama-local` y `embed-local`, costo interno > 0
- [X] T012 Script de arranque del gateway y `.env.example`
- [X] T013 Virtual key de prueba y llamada exitosa

## Fase 2 — Teams, access groups y límites
- [X] T020 `bootstrap.py` idempotente: teams `rrhh`, `desarrollo`, `plataforma`
- [X] T021 Access groups `local-models` / `cloud-models`
- [X] T022 `verify_gateway.py`: válida, modelo no permitido, presupuesto, bloqueada

## Fase 3 — governance
- [X] T030 Modelos: Organization, Area, Sistema, Agente, Notification
- [X] T031 Cliente de la admin API de LiteLLM
- [X] T032 Registro de agentes (key mostrada una vez, regenerar)
- [X] T033 Kill switch (pause/resume → block/unblock)
- [X] T034 Webhook de alertas + monitor de auto-pausa
- [X] T035 Notificaciones

## Fase 4 — agent-lab
- [x] T040 Almacén cifrado de keys
- [x] T041 Grafo Talentia (rama condicional)
- [x] T042 Grafo AgentFactory (bucle de revisión)
- [x] T043 Alta de los 8 agentes en governance + endpoint de ejecución

## Fase 5 — Backend de TokenIO vía gateway
- [x] T050 `ollama_client.py` con modo gateway
- [x] T051 Keys de los 6 agentes y alias de modelos

## Fase 6 — Langfuse
- [ ] T060 Callbacks del gateway sin contenido + metadata por ejecución

## Fase 7 — UI
- [ ] T070 Gobierno · T071 Registro de agentes · T072 Notificaciones · T073 Laboratorio

## Fase 8 — Red local y documentación
- [ ] T080 Modo servidor · T081 README · T082 `docker-compose.yml`
