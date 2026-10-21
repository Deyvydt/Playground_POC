# Agent Playground · TCS

Plataforma para **crear, probar, conectar con conocimiento interno y
administrar agentes de IA** sobre modelos que corren en infraestructura propia
(Ollama), sin depender de un playground público de terceros.

## Capacidades

| Área | Qué permite |
|---|---|
| **Inicio** | Resumen del consumo de tokens, costo evitado frente a la nube, agentes más usados y actividad reciente |
| **Agentes** | Crear y configurar agentes: instrucciones, modelo, temperatura, herramientas; pausar/activar |
| **Conversación** | Chat con historial por usuario y "Ver razonamiento": instrucciones usadas, fragmentos recuperados, llamadas al modelo y herramientas |
| **Conocimiento** | Subir documentos (PDF/TXT/MD) para que el agente responda con información interna |
| **Flujos** | Encadenar agentes; cada respuesta alimenta al siguiente, con progreso en vivo |
| **Consumo** | Tokens de entrada/salida, latencia, errores y costo de referencia por agente, usuario y modelo (7/30/90 días) |
| **Usuarios** | Cuentas con correo y contraseña, roles Administrador / Desarrollador / Usuario, activar o desactivar acceso |

Los permisos se validan en el servidor. Atajos: `Ctrl+K` buscador global,
`Ctrl+B` plegar el menú lateral.

## Stack

- **Modelos**: [Ollama](https://ollama.com) — `llama3.2:3b`, `mistral`,
  `nomic-embed-text` (embeddings).
- **Backend**: Python + FastAPI + SQLModel + SQLite.
- **Frontend**: React + Vite + Tailwind CSS + Recharts + Framer Motion, fuentes
  autoalojadas (Geist, Instrument Serif) e íconos lucide.

## Cómo correrlo

```bash
# 1) Modelos locales
ollama pull llama3.2:3b && ollama pull mistral && ollama pull nomic-embed-text

# 2) Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3) Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

Abrir `http://localhost:5173` e iniciar sesión:

| Correo | Rol | Contraseña |
|---|---|---|
| `ana.rios@tcs.com` | Administrador | `Tcs2026!` |
| `carlos.vega@tcs.com` | Desarrollador | `Tcs2026!` |
| `lucia.soto@tcs.com` | Usuario | `Tcs2026!` |

Guion de demo y solución de problemas en
[`specs/001-agent-playground/quickstart.md`](specs/001-agent-playground/quickstart.md).

## Documentación

| Documento | Contenido |
|---|---|
| [`.specify/memory/constitution.md`](.specify/memory/constitution.md) | Principios del proyecto |
| [`specs/001-agent-playground/spec.md`](specs/001-agent-playground/spec.md) | Historias de usuario y criterios de aceptación |
| [`specs/001-agent-playground/plan.md`](specs/001-agent-playground/plan.md) | Arquitectura y decisiones técnicas |
| [`specs/001-agent-playground/research.md`](specs/001-agent-playground/research.md) | Alternativas evaluadas |
| [`specs/001-agent-playground/data-model.md`](specs/001-agent-playground/data-model.md) | Entidades y relaciones |
| [`specs/001-agent-playground/contracts/api.md`](specs/001-agent-playground/contracts/api.md) | Contrato de la API REST |
| [`specs/001-agent-playground/tasks.md`](specs/001-agent-playground/tasks.md) | Tareas y estado |
| [`AGENTS.md`](AGENTS.md) | Guía para agentes de IA que contribuyan al repo |

## Siguientes pasos

SSO corporativo en lugar del login local, adaptador para modelos en la nube
detrás de `ollama_client.py`, streaming token a token y un vectorstore
dedicado para bases de conocimiento grandes (ver backlog en `tasks.md`).

## Nota sobre la marca

El logo de TCS (`frontend/public/tcs-logo.svg`, `tcs-mark.svg`) proviene del
archivo público en Wikimedia Commons. Para uso fuera de la organización,
reemplazarlo por el asset oficial obtenido internamente.
