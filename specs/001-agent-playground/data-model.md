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
| icon | string | Clave de ícono de la UI (ej. `wrench`, `chart-column`) |
| description | string | Resumen de una línea |
| role_prompt | text | Prompt de sistema — define personalidad y reglas |
| model | string | Nombre del modelo Ollama (ej. `llama3.2:3b`) |
| temperature | float | 0.0–1.0 |
| tools | JSON (list[str]) | Nombres de herramientas habilitadas |
| status | string | `active` \| `inactive` |
| created_by | string | Nombre del usuario que lo creó |
| created_at / updated_at | datetime | |

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
| user_id | int \| null | Dueño de la conversación (cada usuario ve solo las suyas) |
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
| agent_id, agent_name, model | — | Denormalizados para reportes simples (se conservan si el agente se elimina) |
| user_id | int \| null | Usuario que originó el turno (consumo por usuario) |
| latency_ms, prompt_tokens, completion_tokens, total_tokens | int | |
| tool_calls | int | Cantidad de herramientas invocadas en el turno |
| success | bool | |
| error_message | string \| null | |
| created_at | datetime | |

## User
Cuenta con credenciales locales (correo + contraseña) y un rol.

| Campo | Tipo | Notas |
|---|---|---|
| id | int (PK) | |
| name | string | |
| email | string | Único, en minúsculas; identificador de login |
| password_hash | string | PBKDF2-SHA256 con sal (`app/security.py`) |
| role | string | `admin` \| `developer` \| `viewer` |
| title | string | Cargo mostrado en la UI |
| is_active | bool | Una cuenta inactiva no puede iniciar sesión |
| created_at / last_login_at | datetime | |

Las columnas nuevas se agregan automáticamente a bases existentes al iniciar
(`database.py::_migrate`).

## Relaciones

```
Agent 1---N KnowledgeDocument 1---N KnowledgeChunk
Agent 1---N Conversation 1---N Message
Agent 1---N MetricLog
```
