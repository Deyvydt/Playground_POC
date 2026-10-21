# Plan Técnico — TCS Agent Playground

**Entrada**: `spec.md` (mismo directorio) | **Constitución**: `.specify/memory/constitution.md`

## Resumen Técnico

Aplicación de dos capas desplegada localmente: un backend FastAPI que orquesta
llamadas a modelos servidos por Ollama (incluyendo RAG y function-calling), y un
frontend React/Vite que expone las cuatro áreas funcionales del producto
(Agentes, Conocimiento, Playground, Panel/RBAC) sobre una identidad visual TCS.

## Stack

| Capa | Elección | Motivo (ver `research.md`) |
|---|---|---|
| Modelos | Ollama (`llama3.2:3b`, `mistral:latest`, `nomic-embed-text`) | Privacidad + costo $0 |
| Backend | Python 3.12 + FastAPI + SQLModel + SQLite | Simplicidad, tipado, sin infra externa |
| RAG | Chunking propio + embeddings Ollama + cosine similarity (NumPy) | Evita dependencias pesadas para el volumen de un POC |
| Frontend | React 18 + Vite + Tailwind CSS + Recharts + Framer Motion | Control total de UX/marca, carga rápida en demo |
| Autenticación | Tokens HMAC firmados + PBKDF2 (librería estándar de Python) | Sin dependencias nuevas; reemplazable por SSO |
| Documentación | Spec Kit (SDD): constitution → spec → plan → tasks | Trazabilidad de decisiones para la revisión de negocio |

## Estructura del Proyecto

```
Playground_POC/
├── .specify/memory/constitution.md
├── specs/001-agent-playground/{spec,plan,tasks,research,data-model,quickstart}.md
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + lifespan (init_db, seed)
│   │   ├── config.py          # Variables de entorno
│   │   ├── database.py        # Engine + sesión SQLModel
│   │   ├── models.py          # Entidades (ver data-model.md)
│   │   ├── schemas.py         # DTOs de request/response
│   │   ├── ollama_client.py   # Único punto de contacto con el motor de modelos
│   │   ├── rag.py             # Chunking, embeddings, recuperación
│   │   ├── tools.py           # Catálogo + ejecución de herramientas
│   │   ├── orchestrator.py    # Bucle agente: RAG -> LLM -> tools -> traza
│   │   ├── security.py        # Hash de contraseñas, tokens firmados, permisos por rol
│   │   ├── seed.py            # Datos de demostración idempotentes
│   │   └── routers/           # auth, agents, knowledge, chat, orchestration, metrics, users, system
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/             # Login, Home, Agents, AgentDetail, Flows, Usage, UsersPage, SettingsPage
│   │   ├── components/        # Sidebar, PageHeader, CommandPalette, Tooltip, Modal, TracePanel, ChatBubble...
│   │   ├── context/           # SessionContext (sesión + permisos), UIContext (toasts y confirmaciones)
│   │   ├── lib/               # Formato, íconos de agentes, Markdown, navegación
│   │   └── api/client.js      # Cliente HTTP hacia el backend
│   └── public/tcs-logo.svg
└── .claude/skills/            # Automatizaciones del repo (levantar el entorno de demo)
```

## Flujo de un turno de agente (núcleo del sistema)

```
Usuario envía mensaje
   -> ¿el agente tiene conocimiento (RAG)? -> recuperar top-k fragmentos por similitud
   -> construir prompt de sistema (rol + contexto recuperado)
   -> llamar a Ollama /api/chat (con `tools` si el agente los tiene habilitados)
   -> ¿el modelo pidió una herramienta? -> ejecutarla -> reinyectar resultado -> repetir (máx. 3 rondas)
   -> respuesta final
   -> registrar traza + métricas (latencia, tokens) en SQLite
```

Implementado en `backend/app/orchestrator.py::run_agent_turn`, reutilizado tanto
por el endpoint de chat como por el de orquestación multi-agente (donde la salida
de un agente se convierte en la entrada del siguiente).

## Decisiones de UX (resumen — detalle de marca en README)

- Paleta: neutros cálidos (`mist-*`) + casi negro (`ink-*`) con un único acento
  naranja (`accent`, `#E3622E`). Los gráficos usan acento + negro; el texto en
  acento usa `accent-dark` para cumplir contraste.
- Tipografía autoalojada (sin llamadas a CDNs externos): Geist para interfaz,
  Geist Mono para cifras/código e Instrument Serif solo en titulares.
- Íconos de línea (lucide) en lugar de emojis; tooltips en toda acción de solo
  ícono; menú lateral plegable (Ctrl+B) y buscador global (Ctrl+K).
- La interfaz no incluye texto explicativo del proyecto: el producto se
  presenta como herramienta de trabajo, la narrativa la da el presentador.
- Cada gráfico usa un solo eje (nunca doble eje) y colores categóricos en orden
  fijo; ningún estado se comunica solo por color (se usan íconos + etiqueta).
- "Inicio" se adapta al rol: con permiso de métricas muestra consumo, actividad
  y agentes más usados; para usuarios de negocio, los agentes disponibles.

## Riesgos y Mitigaciones

| Riesgo | Mitigación |
|---|---|
| Ollama no está corriendo durante la demo | El encabezado muestra el estado del motor en tiempo real; los endpoints devuelven `503` con mensaje claro y el turno fallido queda registrado en métricas |
| Un modelo no soporta function-calling correctamente | El bucle de orquestación limita a 3 rondas y cae a respuesta de texto si no hay `tool_calls` |
| Tiempo de respuesta de modelos locales (CPU) | Se prioriza `llama3.2:3b` (liviano) para los agentes usados en vivo durante la demo |

## Fuera de Alcance del Plan

Ver sección "Fuera de Alcance" en `spec.md` (SSO corporativo, multi-tenant,
proveedores en la nube, vectorstore dedicado, streaming).
