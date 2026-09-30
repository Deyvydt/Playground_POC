# AGENTS.md

Guía para cualquier agente de IA (Claude Code, Copilot, etc.) que trabaje en este
repositorio. Léela antes de modificar código.

## Qué es este repositorio

"Agent Playground" de TCS: una plataforma interna para crear, probar y
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
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/uvicorn app.main:app --reload --port 8000
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
  `SessionContext` (sesión y permisos) y `UIContext` (toasts y confirmaciones).
  Tailwind con los tokens de `tailwind.config.js` (`ink-*`, `mist-*`,
  `accent-*`) y las clases de `index.css` (`btn-*`, `input`, `card`, `label`) —
  no introducir colores sueltos fuera de esa paleta. Íconos siempre de
  `lucide-react` (nunca emojis); toda acción de solo ícono lleva `Tooltip`.
- **Textos de la interfaz**: sin referencias a "POC", "prototipo", metodología o
  detalles de implementación (RAG, embeddings, nombres de librerías). La UI se
  presenta como producto final; ese contexto vive en la documentación.
- **Seguridad**: toda ruta nueva de `/api` debe depender de `get_current_user` o
  `require("<permiso>")` (`app/security.py`). Los permisos por rol están en
  `PERMISSIONS`; el frontend los consulta con `can()`.
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
- No introducir SSO, multi-tenant o un vectorstore dedicado sin antes
  actualizar `spec.md`/`plan.md` — está explícitamente fuera de alcance de esta
  iteración (Principio V).

## Testing manual

No hay suite de tests automatizados en este POC (fuera de alcance). Antes de dar
un cambio por terminado: levantar backend + frontend, y validar manualmente el
flujo afectado según el guion de `quickstart.md`.
