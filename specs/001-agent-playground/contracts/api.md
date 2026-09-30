# Contrato de API — TCS Agent Playground

Base URL en desarrollo: `http://localhost:8000` (el frontend accede vía proxy
`/api` configurado en `vite.config.js`). Documentación interactiva autogenerada
disponible en `http://localhost:8000/docs` (Swagger UI de FastAPI).

Todas las rutas, salvo `/api/health` y `/api/auth/login`, requieren el header
`Authorization: Bearer <token>`. Sin token válido responden `401`; sin el
permiso del rol, `403`.

## Autenticación

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/auth/login` | Body `{email, password}` → `{token, user}` (token firmado, expira según `TOKEN_TTL_HOURS`) |
| GET | `/api/auth/me` | Usuario de la sesión, incluye su lista de `permissions` |

## Sistema

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Estado del backend y disponibilidad de Ollama |
| GET | `/api/models` | Modelos locales instalados en Ollama |
| GET | `/api/tools` | Catálogo de herramientas (function calling) disponibles |
| GET | `/api/roles` | Permisos de cada rol |

## Agentes

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/agents` | Lista todos los agentes |
| POST | `/api/agents` | Crea un agente (permiso `create`) |
| GET | `/api/agents/{id}` | Detalle de un agente |
| PUT | `/api/agents/{id}` | Actualiza campos de un agente, incluido `status` (permiso `edit`) |
| DELETE | `/api/agents/{id}` | Elimina un agente con sus conversaciones y documentos; las métricas se conservan (permiso `delete`) |

## Conocimiento (RAG)

Subir y eliminar requiere el permiso `knowledge`. Formatos: PDF, TXT, MD (máx. 10 MB).

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/agents/{id}/knowledge` | Lista documentos indexados de un agente |
| POST | `/api/agents/{id}/knowledge` | Sube y fragmenta/embebe un documento (`multipart/form-data`, campo `file`) |
| DELETE | `/api/agents/knowledge/{document_id}` | Elimina un documento y sus fragmentos |

## Chat

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/agents/{id}/conversations` | Lista las conversaciones del usuario con un agente |
| DELETE | `/api/conversations/{id}` | Elimina una conversación propia |
| GET | `/api/conversations/{id}/messages` | Historial de una conversación |
| POST | `/api/agents/{id}/chat` | Envía un mensaje; body `{message, conversation_id?}` — devuelve `{conversation_id, message, trace, latency_ms, prompt_tokens, completion_tokens}`. `503` si el motor de modelos no responde, `409` si el agente está pausado |

## Orquestación multi-agente

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/orchestration/run` | Body `{input_text, pipeline: [agent_id, ...]}` — ejecuta la cadena en orden y devuelve `{steps: [...], final_output}` |
| POST | `/api/orchestration/stream` | Mismo body; responde NDJSON con eventos `start`, `step`, `error` y `done` a medida que avanza cada agente |

## Métricas

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/metrics/summary?days=30` | Totales (tokens de entrada/salida, latencia, tasa de error), desglose por agente, modelo y usuario, y costo local vs. nube de referencia |
| GET | `/api/metrics/timeseries?days=14&agent_id=` | Solicitudes y tokens (entrada/salida) por día, opcionalmente de un solo agente |
| GET | `/api/metrics/activity?limit=8` | Últimos turnos ejecutados (permiso `metrics`) |

## Usuarios

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/users` | Lista usuarios |
| POST | `/api/users` | Crea un usuario `{name, email, title, role, password}` (permiso `manage_users`) |
| PUT | `/api/users/{id}` | Actualiza datos, rol, estado o contraseña (permiso `manage_users`; un admin no puede degradarse ni desactivarse a sí mismo) |
| DELETE | `/api/users/{id}` | Elimina un usuario (permiso `manage_users`; no aplica a la propia cuenta) |
