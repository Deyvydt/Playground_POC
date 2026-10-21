# Tareas — Automatización de pruebas

Generado a partir de `plan.md`.

## Fase 1 — Diseño y planificación
- [x] T001 Estrategia, niveles, dobles de prueba y matriz de trazabilidad (`plan.md`)
- [x] T002 Criterios de aceptación numerados (`CA-N.M`) en `specs/001` y `specs/002`
- [x] T003 Escenarios Gherkin en español: 7 `.feature` de spec 001, 5 de spec 002

## Fase 2 — Infraestructura
- [x] T010 `tests/requirements.txt` (entorno único) y `tests/pytest.ini`
- [x] T011 Plugin de clasificación y resultados (`tests/reporting_plugin.py`)
- [x] T012 Dobles: `FakeLLM` (backend), `FakeGateway` (governance), `FakeChatModel` (agent-lab)

## Fase 3 — Pruebas técnicas
- [x] T020 Backend: unitarias (herramientas, RAG, seguridad, orquestador, cliente de modelos)
- [x] T021 Backend: API (auth, agentes, chat, conocimiento, usuarios, consumo, sistema, flujos)
- [x] T022 Governance: unitarias (registro, monitor, auth delegada, config del gateway) y API
- [x] T023 Agent-lab: unitarias (rutas de grafos, errores, secretos) y API
- [x] T024 Contrato con Schemathesis para los tres OpenAPI

## Fase 4 — Pruebas funcionales
- [x] T030 Pasos Gherkin del backend (spec 001 + spec 002 US-7)
- [x] T031 Pasos Gherkin de governance (spec 002 US-2, US-3, US-4)
- [x] T032 Pasos Gherkin de agent-lab (spec 002 US-6)

## Fase 5 — Ejecución y reporte
- [x] T040 `scripts/run-tests.py`: suites por proceso, filtros, código de salida
- [x] T041 Reporte HTML, Markdown, JSON y JUnit con matriz de trazabilidad
- [x] T042 Lanzadores `run-tests.ps1` (Windows) y `run-tests.sh` (Linux/CI)

## Fase 6 — SDD
- [x] T050 Agente `disenador-pruebas` (`.claude/agents/`)
- [x] T051 Skills `sdd-pruebas` y `sdd-specs` (`.claude/skills/`)
- [x] T052 Specs, quickstart y `AGENTS.md` actualizados

## Defectos encontrados por las pruebas (corregidos)
- [x] D001 `POST /api/agents/{id}/knowledge` respondía `{}`: el objeto expiraba tras el
  commit y la interfaz mostraba "“undefined” indexado en undefined fragmentos"
  (`backend/app/rag.py`).
- [x] D002 Un id mayor que el entero de 64 bits de SQLite daba 500 en todas las rutas
  con id (`backend/app/main.py`, ahora 404). Encontrado por Schemathesis.
- [x] D003 Un token no ASCII en el webhook de alertas daba 500 (`compare_digest` con
  `str`). Mismo riesgo en `X-Service-Token` de governance y agent-lab, y en la firma
  del token de sesión del backend. Ahora se comparan bytes. Encontrado por Schemathesis.
- [x] D004 El webhook de alertas daba 500 con un cuerpo que no es JSON (ahora 400).

## Hallazgos abiertos (decisión de producto)
- [ ] H001 `GET /api/metrics/summary` y `/api/metrics/timeseries` solo exigen sesión,
  aunque el rol "solo lectura" no tiene el permiso `metrics` (la interfaz le oculta
  Consumo; `/api/metrics/activity` sí lo exige). La página Agentes usa
  `metricsSummary` para todos los roles, por eso no se cambió sin decidirlo.

## Siguiente iteración (integración de sistemas)
- [ ] T060 Pruebas E2E del frontend (Playwright) para Gobierno, Laboratorio y permisos visuales
- [ ] T061 Pruebas de integración con LiteLLM + Postgres reales (docker compose) y Ollama
- [ ] T062 Workflow de GitHub Actions que ejecute `scripts/run-tests.py` y publique `reports/`
