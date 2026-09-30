# Contrato de API — TCS Agent Playground

Base URL en desarrollo: `http://localhost:8000` (el frontend accede vía proxy
`/api` configurado en `vite.config.js`). Documentación interactiva autogenerada
disponible en `http://localhost:8000/docs` (Swagger UI de FastAPI).

## Sistema

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Estado del backend y disponibilidad de Ollama |
| GET | `/api/models` | Modelos locales instalados en Ollama |
| GET | `/api/tools` | Catálogo de herramientas (function calling) disponibles |

## Agentes

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/agents` | Lista todos los agentes |
| POST | `/api/agents` | Crea un agente |
| GET | `/api/agents/{id}` | Detalle de un agente |
| PUT | `/api/agents/{id}` | Actualiza campos de un agente |
| DELETE | `/api/agents/{id}` | Elimina un agente |

## Conocimiento (RAG)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/agents/{id}/knowledge` | Lista documentos indexados de un agente |
| POST | `/api/agents/{id}/knowledge` | Sube y fragmenta/embebe un documento (`multipart/form-data`, campo `file`) |
| DELETE | `/api/agents/knowledge/{document_id}` | Elimina un documento y sus fragmentos |

## Chat

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/agents/{id}/conversations` | Lista conversaciones de un agente |
| GET | `/api/conversations/{id}/messages` | Historial de una conversación |
| POST | `/api/agents/{id}/chat` | Envía un mensaje; body `{message, conversation_id?}` — devuelve `{conversation_id, message, trace, latency_ms, prompt_tokens, completion_tokens}` |

## Orquestación multi-agente

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/orchestration/run` | Body `{input_text, pipeline: [agent_id, ...]}` — ejecuta la cadena en orden y devuelve `{steps: [...], final_output}` |

## Métricas

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/metrics/summary` | Totales, promedio de latencia, desglose por agente, comparación de costo local vs. nube de referencia |
| GET | `/api/metrics/timeseries` | Solicitudes y tokens por día (últimos 7 días) |

## Usuarios (RBAC simulado)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/users` | Lista los usuarios de demostración (admin/developer/viewer) |
