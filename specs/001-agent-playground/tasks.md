# Tareas — TCS Agent Playground

Generado a partir de `plan.md`. Marcado según el estado de esta primera
iteración del POC (todas las tareas P1–P2 completadas para la demo).

## Fase 1 — Fundacional
- [X] T001 Estructura de carpetas backend/frontend + entorno virtual/npm
- [X] T002 Configuración base FastAPI (`main.py`, CORS, lifespan)
- [X] T003 Modelos de datos SQLModel (`models.py`) — ver `data-model.md`
- [X] T004 Cliente único de Ollama (`ollama_client.py`) — chat, embeddings, listado de modelos

## Fase 2 — US-1: Crear y configurar agentes
- [X] T010 Endpoints CRUD de agentes (`routers/agents.py`)
- [X] T011 Formulario de creación/edición en frontend (`AgentFormModal.jsx`)
- [X] T012 Listado de agentes con estado y metadatos (`Agents.jsx`, `AgentCard.jsx`)
- [X] T013 Datos de demostración sembrados al iniciar (`seed.py`)

## Fase 3 — US-2: Playground de chat con trazabilidad
- [X] T020 Bucle de orquestación de un turno (`orchestrator.py::run_agent_turn`)
- [X] T021 Catálogo y ejecución de herramientas (`tools.py`)
- [X] T022 Endpoint de chat con persistencia de conversación/mensajes (`routers/chat.py`)
- [X] T023 UI de chat + panel de traza colapsable (`ChatBubble.jsx`, `TracePanel.jsx`)

## Fase 4 — US-3: Conocimiento interno (RAG)
- [X] T030 Extracción de texto (.txt/.pdf) y chunking (`rag.py`)
- [X] T031 Generación y almacenamiento de embeddings (Ollama `nomic-embed-text`)
- [X] T032 Recuperación por similitud coseno e inyección en el prompt de sistema
- [X] T033 Endpoints de subida/listado/eliminación de documentos (`routers/knowledge.py`)
- [X] T034 UI de carga de documentos con drag & drop (`KnowledgeTab` en `AgentDetail.jsx`)
- [X] T035 Documento de ejemplo (manual de bienvenida) sembrado para el agente "Asesor de Onboarding"

## Fase 5 — US-4: Orquestación multi-agente
- [X] T040 Endpoint de pipeline secuencial (`routers/orchestration.py`)
- [X] T041 UI de construcción de pipeline + visualización de pasos (`MultiAgentFlow.jsx`)

## Fase 6 — US-5: Monitoreo y costos
- [X] T050 Registro de métricas por turno (`MetricLog` en `orchestrator.py`)
- [X] T051 Endpoints de resumen y serie temporal (`routers/metrics.py`)
- [X] T052 Panel con KPIs y gráficos validados (`Dashboard.jsx`)
- [X] T053 Comparación de costo local ($0) vs. referencia de nube

## Fase 7 — US-6: RBAC simulado
- [X] T060 Endpoint y modelo de usuarios (`routers/users.py`, `models.User`)
- [X] T061 Contexto de sesión simulada en frontend (`SessionContext.jsx`)
- [X] T062 Selector de usuario/rol en `TopBar.jsx` + página de RBAC (`SettingsPage.jsx`)
- [X] T063 Reglas de visibilidad de acciones según rol (`can()` en `SessionContext`)

## Fase 8 — Presentación e identidad
- [X] T070 Página "Resumen" orientada a audiencia no técnica (`Overview.jsx`)
- [X] T071 Identidad visual TCS: logo oficial + paleta validada (`tcs-logo.svg`, `tailwind.config.js`)

## Fase 9 — Documentación (SDD)
- [X] T080 Constitución del proyecto (`.specify/memory/constitution.md`)
- [X] T081 Especificación funcional (`spec.md`)
- [X] T082 Plan técnico (`plan.md`), investigación (`research.md`), modelo de datos (`data-model.md`)
- [X] T083 Contrato de API (`contracts/api.md`) y guía de inicio rápido (`quickstart.md`)
- [X] T084 `AGENTS.md` (guía para agentes de IA que trabajen en este repo) y `README.md`

## Fase 10 — Iteración 2: producto demostrable
- [X] T100 Login con correo y contraseña (hash PBKDF2, tokens firmados) — `security.py`, `routers/auth.py`
- [X] T101 Permisos validados en el servidor para todas las rutas (`require(permiso)`)
- [X] T102 Gestión de usuarios: crear, editar, desactivar, eliminar (`routers/users.py`, `UsersPage.jsx`)
- [X] T103 Consumo por agente, modelo y usuario con filtro de periodo (`routers/metrics.py`, `Usage.jsx`)
- [X] T104 Migración automática de bases existentes (`database.py::_migrate`)
- [X] T105 Rediseño visual: paleta negro/blanco + naranja, íconos en lugar de emojis, tipografía autoalojada
- [X] T106 Menú lateral plegable, tooltips, buscador global (Ctrl+K), toasts y confirmaciones
- [X] T107 Historial de conversaciones por usuario, sugerencias de inicio y Markdown en respuestas
- [X] T108 Flujos con progreso en vivo (`/api/orchestration/stream`)
- [X] T109 Manejo controlado de fallas del motor de modelos (503 + métrica fallida + traza)
- [X] T110 Eliminación de textos internos de la interfaz ("POC", "prototipo", metodología)

## Backlog explícito (fuera de esta iteración)

- [ ] T090 SSO corporativo (reemplazar el login local)
- [ ] T091 Adaptador de modelo en la nube (OpenAI/Anthropic) tras `ollama_client`
- [ ] T092 Streaming de respuestas token-a-token
- [ ] T093 Vectorstore dedicado para RAG a mayor escala
