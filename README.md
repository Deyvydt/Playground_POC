# TCS Agent Playground — Prototipo (POC)

Entorno propio para **crear, probar, conectar con conocimiento interno y
administrar agentes de IA**, corriendo sobre modelos locales (sin depender de
un playground público de terceros).

Prototipo desarrollado para presentar la propuesta a la Gerencia Regional:
demuestra con funcionalidad real — no mockups — por qué construir una
plataforma propia de agentes tiene sentido para TCS.

## Por qué esto importa

| Beneficio | Cómo lo demuestra este POC |
|---|---|
| Privacidad de datos | Los modelos corren localmente (Ollama); nada sale de la máquina/infraestructura de TCS |
| Independencia de proveedores | El modelo de cada agente se elige por configuración, no está acoplado al código |
| Colaboración multi-agente | Un flujo real encadena un agente "Analista" con un agente "Redactor" |
| Personalización absoluta | Interfaz propia, en español, con la identidad visual de TCS |
| Costo | $0 marginal por consulta (modelos locales) vs. el costo por token de una API comercial |

## Las 4 áreas funcionales

1. **Agentes** — creación y configuración: rol (prompt de sistema), modelo,
   temperatura y herramientas (function calling).
2. **Conocimiento (RAG)** — subir documentos internos; el agente responde con
   esa información, con trazabilidad de qué fragmento usó y su similitud.
3. **Playground** — chat en vivo con inspección paso a paso del razonamiento
   del agente (prompt usado, recuperación RAG, llamadas a herramientas).
4. **Panel / RBAC** — consumo de tokens, latencia y costo por agente; control
   de accesos simulado por rol (Administrador / Desarrollador / Solo lectura).

## Stack técnico

- **Modelos**: [Ollama](https://ollama.com) local — `llama3.2:3b`, `mistral`,
  `nomic-embed-text` (embeddings para RAG).
- **Backend**: Python + FastAPI + SQLModel + SQLite.
- **Frontend**: React + Vite + Tailwind CSS + Recharts + Framer Motion.
- **Metodología**: Spec-Driven Development (SDD) siguiendo la estructura de
  [GitHub Spec Kit](https://github.com/github/spec-kit).

## Cómo correrlo

Ver la guía completa en
[`specs/001-agent-playground/quickstart.md`](specs/001-agent-playground/quickstart.md).
Resumen:

```bash
# 1) Modelos locales
ollama pull llama3.2:3b && ollama pull mistral && ollama pull nomic-embed-text

# 2) Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3) Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

Abrir `http://localhost:5173`.

## Documentación (SDD)

| Documento | Contenido |
|---|---|
| [`.specify/memory/constitution.md`](.specify/memory/constitution.md) | Principios no negociables del proyecto |
| [`specs/001-agent-playground/spec.md`](specs/001-agent-playground/spec.md) | Historias de usuario y criterios de aceptación |
| [`specs/001-agent-playground/plan.md`](specs/001-agent-playground/plan.md) | Arquitectura y decisiones técnicas |
| [`specs/001-agent-playground/research.md`](specs/001-agent-playground/research.md) | Alternativas evaluadas y por qué se descartaron |
| [`specs/001-agent-playground/data-model.md`](specs/001-agent-playground/data-model.md) | Entidades y relaciones |
| [`specs/001-agent-playground/contracts/api.md`](specs/001-agent-playground/contracts/api.md) | Contrato de la API REST |
| [`specs/001-agent-playground/tasks.md`](specs/001-agent-playground/tasks.md) | Desglose de tareas y estado |
| [`AGENTS.md`](AGENTS.md) | Guía para agentes de IA que contribuyan a este repo |

## Alcance y límites de este POC

Es un prototipo de evaluación, no un sistema productivo. Explícitamente fuera
de alcance por ahora (ver `spec.md`): autenticación real / SSO corporativo,
multi-tenant, proveedores de modelo en la nube, vectorstore dedicado a gran
escala y streaming token-a-token. El siguiente paso natural, si la Gerencia
aprueba la iniciativa, es priorizar ese backlog para una versión productiva.

## Nota sobre la marca

El logo de TCS incluido (`frontend/public/tcs-logo.svg`) proviene del archivo
público en Wikimedia Commons y se usa aquí únicamente con fines de
demostración interna. Para cualquier uso más allá de este POC, reemplazar por
el asset oficial de la marca obtenido internamente.
