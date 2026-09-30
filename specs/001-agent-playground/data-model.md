# Modelo de Datos — TCS Agent Playground

Todas las entidades se persisten en SQLite (`backend/data/playground.db`) vía
SQLModel. Este documento describe el "qué", no el código — ver `backend/app/models.py`
para la implementación.

## Agent
Representa un agente configurable.

| Campo | Tipo | Notas |
|---|---|---|
| id | int (PK) | |
| name | string | |
| avatar_emoji | string | Identidad visual rápida en la UI |
| description | string | Resumen de una línea |
| role_prompt | text | Prompt de sistema — define personalidad y reglas |
| model | string | Nombre del modelo Ollama (ej. `llama3.2:3b`) |
| temperature | float | 0.0–1.0 |
| tools | JSON (list[str]) | Nombres de herramientas habilitadas |
| status | string | `active` \| `inactive` |
| created_by | string | Nombre del usuario (simulado) |
| created_at | datetime | |

## KnowledgeDocument
Un archivo subido a la base de conocimiento de un agente.

| Campo | Tipo | Notas |
|---|---|---|
| id | int (PK) | |
| agent_id | int (FK -> Agent) | |
| filename | string | |
| chunk_count | int | Cantidad de fragmentos generados |
| uploaded_at | datetime | |

## KnowledgeChunk
Un fragmento de texto embebido, usado para recuperación (RAG).

| Campo | Tipo | Notas |
|---|---|---|
| id | int (PK) | |
| document_id | int (FK -> KnowledgeDocument) | |
| agent_id | int (FK -> Agent) | Denormalizado para consultas rápidas |
| chunk_index | int | Orden dentro del documento |
| content | text | Texto del fragmento (~800 caracteres) |
| embedding | JSON (list[float]) | Vector generado por `nomic-embed-text` |

## Conversation
Una sesión de chat entre un usuario y un agente.

| Campo | Tipo | Notas |
|---|---|---|
| id | int (PK) | |
| agent_id | int (FK -> Agent) | |
| title | string | Derivado del primer mensaje |
| started_at | datetime | |

## Message
Un turno dentro de una conversación.

| Campo | Tipo | Notas |
|---|---|---|
| id | int (PK) | |
| conversation_id | int (FK -> Conversation) | |
| role | string | `user` \| `assistant` |
| content | text | |
| trace | JSON (list[dict]) | Pasos de razonamiento (solo en turnos del agente) |
| latency_ms | int | |
| prompt_tokens / completion_tokens | int | Provenientes de la respuesta de Ollama |
| created_at | datetime | |

## MetricLog
Un registro de auditoría/consumo por cada turno ejecutado (chat u orquestación).

| Campo | Tipo | Notas |
|---|---|---|
| id | int (PK) | |
| agent_id, agent_name, model | — | Denormalizados para reportes simples |
| latency_ms, prompt_tokens, completion_tokens, total_tokens | int | |
| tool_calls | int | Cantidad de herramientas invocadas en el turno |
| success | bool | |
| error_message | string \| null | |
| created_at | datetime | |

## User (RBAC simulado)
No hay autenticación real; representa el "usuario simulado" activo en la sesión.

| Campo | Tipo | Notas |
|---|---|---|
| id | int (PK) | |
| name | string | |
| role | string | `admin` \| `developer` \| `viewer` |
| avatar_emoji | string | |
| title | string | Cargo mostrado en la UI |

## Relaciones

```
Agent 1---N KnowledgeDocument 1---N KnowledgeChunk
Agent 1---N Conversation 1---N Message
Agent 1---N MetricLog
```
