# AGENTS.md

Guía para cualquier agente de IA (Claude Code, Copilot, etc.) que trabaje en este
repositorio. Léela antes de modificar código.

## Qué es este repositorio

POC de "TCS Agent Playground": una plataforma interna para crear, probar y
administrar agentes de IA con modelos locales (Ollama). Ver
`specs/001-agent-playground/spec.md` para el alcance funcional completo y
`.specify/memory/constitution.md` para los principios no negociables del
proyecto (privacidad de datos, independencia de proveedores, trazabilidad, UX
minimalista, simplicidad de alcance).

Este proyecto sigue **SDD (Spec-Driven Development)** al estilo GitHub Spec Kit:
los cambios de alcance relevantes deberían reflejarse primero en
`specs/001-agent-playground/{spec,plan,tasks}.md`, no solo en el código.

## Arquitectura en una vista

```
Ollama (localhost:11434) <-- único punto de contacto: backend/app/ollama_client.py
        ^
        |
FastAPI (backend/, puerto 8000) --SQLite--> backend/data/playground.db
        ^
        | /api/* (proxy de Vite)
React + Vite (frontend/, puerto 5173)
```

- El núcleo funcional es `backend/app/orchestrator.py::run_agent_turn`: RAG →
  LLM → (tool-calling opcional) → traza + métricas. Tanto el chat 1-a-1
  (`routers/chat.py`) como la orquestación multi-agente
  (`routers/orchestration.py`) reutilizan esta función.
- Nunca llames a Ollama directamente desde un router — pasa siempre por
  `app/ollama_client.py` (Principio II de la constitución: independencia de
  proveedores).
- El frontend no tiene estado de servidor propio: todo viene de `backend/app/api`
  vía `frontend/src/api/client.js`.

## Cómo correr el proyecto

Ver `specs/001-agent-playground/quickstart.md` para el paso a paso completo.
Resumen:
```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
# Frontend
cd frontend && npm install && npm run dev
```
Requiere Ollama corriendo con `llama3.2:3b`, `mistral` y `nomic-embed-text`
descargados (este último es obligatorio para que el RAG funcione).

## Convenciones de código

- **Backend**: Python + FastAPI + SQLModel. Los routers son delgados; la lógica
  de negocio vive en `app/orchestrator.py`, `app/rag.py`, `app/tools.py`. Sin
  comentarios explicativos de "qué hace" el código — solo el porqué cuando no es
  obvio (ver estilo ya usado en el repo).
- **Frontend**: React funcional + hooks, sin gestor de estado global más allá de
  `SessionContext` (RBAC simulado). Tailwind con los tokens definidos en
  `tailwind.config.js` (`ink-*`, `mist-*`, `tcs-*`) — no introducir colores
  sueltos fuera de esa paleta.
- **Idioma**: toda la interfaz y los textos de cara al usuario están en español
  (audiencia interna de TCS). El código (nombres de variables/funciones) está en
  inglés salvo los nombres de herramientas (`calculadora`, `fecha_actual`, etc.)
  que el modelo invoca literalmente.
- **Datos de demostración**: cualquier agente/documento de ejemplo nuevo debe
  agregarse en `backend/app/seed.py` de forma idempotente (verificar si ya
  existe antes de insertar).

## Qué NO hacer (alineado con la constitución)

- No agregar una llamada directa a una API de modelo en la nube sin pasar por un
  adaptador equivalente a `ollama_client.py` — rompe el Principio II.
- No agregar un paso del agente que no quede reflejado en la `trace` devuelta —
  rompe el Principio III (Observabilidad).
- No introducir autenticación real, multi-tenant o un vectorstore dedicado sin
  antes actualizar `spec.md`/`plan.md` — está explícitamente fuera de alcance de
  esta iteración (Principio V).

## Testing manual

No hay suite de tests automatizados en este POC (fuera de alcance). Antes de dar
un cambio por terminado: levantar backend + frontend, y validar manualmente el
flujo afectado según el guion de `quickstart.md`.
