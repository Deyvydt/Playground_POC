# Fases pendientes — Gobierno de LLMs en TokenIO

Guía para continuar la implementación en otra máquina. Contexto completo de la
sesión en `RESUMEN_SESION.md`; especificación en `specs/002-llm-gateway/`.

**Estado al 2026-10-16**: Fases 0, 1, 2, 3, 4 y 5 terminadas y probadas.
**Faltan 3 fases: 6, 7 y 8.**

---

## 0. Poner en marcha lo ya hecho en una máquina nueva

Los `.env`, los entornos virtuales (`.venv`) y los datos de Postgres
(`services/.data/`) **no están en git**. Hay que recrearlos:

```bash
# 1) Gateway (LiteLLM + Postgres embebido)
cd services/gateway
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # en Linux/Mac: .venv/bin/python
cp .env.example .env
#   Editar .env: LITELLM_MASTER_KEY y LITELLM_SALT_KEY con valores aleatorios que empiecen por "sk-"
#   python -c "import secrets;print('sk-'+secrets.token_urlsafe(24))"
.venv/Scripts/python start.py            # arranca Postgres (:5433) + gateway (:4000); la 1ª vez genera el cliente Prisma
# en otra terminal:
.venv/Scripts/python bootstrap.py        # crea teams rrhh / desarrollo / plataforma
.venv/Scripts/python verify_gateway.py   # debe dar 4/4

# 2) Governance
cd services/governance
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env
#   LITELLM_MASTER_KEY = la misma del gateway
#   SERVICE_TOKEN y WEBHOOK_TOKEN = valores aleatorios
#   Copiar WEBHOOK_TOKEN dentro de WEBHOOK_URL en services/gateway/.env y reiniciar el gateway
.venv/Scripts/python -m uvicorn app.main:app --port 8100     # docs en http://127.0.0.1:8100/docs

# 3) Backend y frontend de TokenIO (como siempre, ver specs/001-agent-playground/quickstart.md)
```

Notas:
- En Windows instalar en rutas cortas (por eso el `.venv` va dentro de cada
  servicio): la ruta de LiteLLM supera 260 caracteres si se instala en carpetas
  muy profundas.
- `certs.py` agrega las CA de Windows (necesario en la red de TCS por inspección
  TLS). En casa no estorba.
- Modelos en Ollama: `config.yaml` usa `llama-3.2-3b-it:latest` y
  `gte-large:latest` (los que había en la máquina de TCS). En tu máquina
  ajusta los `model:` de `services/gateway/config.yaml` a los que tengas
  (`ollama list`), p. ej. `ollama_chat/llama3.2:3b` y `ollama/nomic-embed-text`.
  Los alias que ven los clientes (`llama-local`, `embed-local`) no cambian.
- Con Docker disponible (tu máquina) se puede reemplazar pgserver por un
  Postgres en contenedor: solo cambia `DATABASE_URL` (ver Fase 8).

---

## Fase 4 — Microservicio `agent-lab` (agentes LangGraph de prueba) ✅ terminada

Implementada y probada de punta a punta el 2026-10-16: los dos grafos corren contra
el modelo local vía gateway, el gasto de cada nodo aparece en `GET /gov/agents`, y
pausar un nodo (ej. `revisor_codigo`) corta el grafo en ese nodo con mensaje claro.
`provision.py` es idempotente (confirmado corriéndolo dos veces).

Puesta en marcha en una máquina nueva: igual que gateway/governance (venv propio +
`.env` desde `.env.example` + `SERVICE_TOKEN` igual al de governance), luego:
```bash
cd services/agent-lab
.venv/Scripts/python provision.py                              # registra los 8 nodos
.venv/Scripts/python -m uvicorn app.main:app --port 8200        # docs en /docs
```

**Objetivo** (contexto de diseño, ya aplicado): simular los sistemas Talentia (RR.HH.) y AgentFactory (Desarrollo)
con agentes reales hechos en LangGraph que consumen el modelo **solo** vía
gateway con virtual keys emitidas por governance. Es también el embrión de la
Opción 1 (agentes alojados en TokenIO).

**Estructura** (`services/agent-lab/`, FastAPI en :8200, base propia `agentlab`
en el mismo Postgres — agregarla a `DATABASES` en `services/gateway/start_db.py`):
```
app/main.py, config.py
app/secrets.py          # guarda keys cifradas con Fernet (lib cryptography); clave en .env (LAB_FERNET_KEY)
app/llm.py              # fábrica: ChatOpenAI(base_url=GATEWAY_URL+"/v1", api_key=<key del nodo>, model="llama-local")
app/graphs/talentia.py
app/graphs/agentfactory.py
app/routers/runs.py     # POST /lab/runs/{sistema} -> resultado + traza por nodo
provision.py            # registra los 8 agentes en governance (X-Service-Token) y guarda sus keys cifradas; idempotente
```

**Grafos** (un nodo = un agente = una virtual key):
- Talentia "Proceso de selección": `analizador_cv` → `evaluador_ajuste` (devuelve
  puntaje 0-100) → arista condicional: puntaje ≥ 70 → `generador_entrevista`;
  si no → `redactor_comunicaciones` (rechazo amable). Entrada: CV + descripción
  de la vacante.
- AgentFactory "Fábrica Quarkus": `generador_codigo` (recurso REST + entidad
  Panache) → `revisor_codigo` → si hay observaciones y rondas < 2 vuelve a
  `generador_codigo`; si no → `generador_tests` (JUnit 5 + RestAssured) →
  `documentador`. Entrada: requerimiento en texto.

**Detalles**:
- Dependencias: `langgraph`, `langchain-openai`, `cryptography`, fastapi, httpx.
  **Verificar la API actual en la doc oficial** (StateGraph, START/END,
  `add_conditional_edges`) y fijar versiones.
- Cada llamada envía `extra_body={"metadata": {"agent_id", "sistema", "area",
  "run_id", "generation_name": <nodo>}}` para la trazabilidad (Fase 6).
- Si el gateway responde 401 (agente pausado) o 422/400 (presupuesto), el nodo
  registra el error en la traza y el grafo termina con un mensaje claro en español.
- La respuesta de `/lab/runs` incluye por nodo: entrada resumida, salida,
  tokens, latencia y estado (Principio III de la constitución).
- Auth de `/lab/*`: igual que governance (copiar `app/auth.py`).

**Aceptación** ✅: correr ambos grafos → en `GET /gov/agents` sube el gasto de cada
agente y de su área; pausar `revisor_codigo` en governance → la ejecución de
AgentFactory falla en ese nodo con mensaje claro.

---

## Fase 5 — Los 6 agentes actuales de TokenIO pasan por el gateway ✅ terminada

Implementada y probada de punta a punta el 2026-10-16 (chat, tool-calling, RAG,
`GET /api/models` con alias del gateway, gasto por agente en `plataforma`, kill
switch con mensaje claro). Activar en una máquina nueva: agregar al `.env` del
backend `LLM_GATEWAY_URL`, `GOVERNANCE_URL`, `SERVICE_TOKEN` (igual al de
governance) y `GATEWAY_FERNET_KEY` propia (ver `.env.example`). Al arrancar,
`gateway_keys.register_missing` da de alta en governance los agentes que
todavía no tengan `gateway_key_enc`. Si la base ya existía antes de esta fase,
sumarle la columna a mano una vez: `ALTER TABLE agent ADD COLUMN
gateway_key_enc TEXT` (SQLite no migra solo).

⚠️ Toca código existente del backend (avisar/revisar antes de mezclar).

- `backend/app/ollama_client.py`: si existe `LLM_GATEWAY_URL` en `.env`,
  `chat()` llama a `POST {gateway}/v1/chat/completions` y `embed()` a
  `/v1/embeddings` (alias `embed-local`) con la virtual key del agente, y
  **traduce la respuesta OpenAI al formato actual de Ollama**
  (`{"message": {...}, "prompt_eval_count", "eval_count"}`; los
  `tool_calls[].function.arguments` vienen como string JSON) para que
  `orchestrator.py` y `rag.py` no cambien. Sin `LLM_GATEWAY_URL` sigue el
  camino directo a Ollama (Principio I).
- `chat()` necesita saber qué key usar: agregar parámetro `api_key` opcional y
  pasarlo desde `orchestrator.run_agent_turn` (único cambio ahí).
- `Agent` (backend/app/models.py) gana `gateway_key_enc` (key cifrada con Fernet).
- `seed.py`: modelos de los agentes → alias (`llama-local`); al arrancar, si el
  agente no tiene key, lo registra en governance (sistema `tokenio`, área
  `plataforma`) con `X-Service-Token` y guarda la key cifrada. Idempotente.
- `routers/system.py::models` debería listar los alias del gateway
  (`GET /v1/models` con cualquier key válida) en vez de los modelos de Ollama.
- Errores 401/422 del gateway → mensaje en español ("El agente está pausado por
  un administrador" / "El agente agotó su presupuesto").

**Aceptación** ✅: chat y flujos funcionan igual; su consumo aparece en
`plataforma`; pausar "Soporte TI" en governance bloquea su chat con mensaje claro.

---

## Fase 6 — Langfuse (trazas)

- Crear proyecto en Langfuse Cloud (o self-hosted con Docker en tu máquina).
- `services/gateway/config.yaml`:
  ```yaml
  litellm_settings:
    success_callback: ["langfuse"]
    failure_callback: ["langfuse"]
    turn_off_message_logging: true   # solo tokens/costo/latencia, sin texto (mientras sea Cloud)
  ```
  y en `services/gateway/.env`: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`,
  `LANGFUSE_HOST`. **Verificar en docs.litellm.ai/docs/proxy/logging** (la
  sintaxis puede haber cambiado).
- Clientes envían en `metadata`: `trace_id` por ejecución de grafo,
  `generation_name` = nodo, `tags` = `["agent:<id>", "area:<x>", "sistema:<y>"]`.
- Opcional: en agent-lab, callback de Langfuse para LangChain (una traza por
  grafo, un span por nodo) con enmascarado (`mask`).

**Aceptación**: en Langfuse se ven trazas por agente con tokens, costo,
latencia y errores, sin el texto de los prompts.

---

## Fase 7 — UI en TokenIO

⚠️ Toca el frontend. Respetar AGENTS.md: paleta `ink/mist/accent`, clases
`btn-*`, `input`, `card`, íconos `lucide-react` + `Tooltip`, textos en español
sin mencionar librerías ni "POC".

- `frontend/vite.config.js`: proxy `/gov` → `http://127.0.0.1:8100` y `/lab` →
  `http://127.0.0.1:8200`. El token de sesión actual se envía igual
  (`Authorization: Bearer`).
- **Gobierno**: áreas (gasto vs presupuesto del team) → sistemas → agentes
  (estado, gasto/presupuesto, última actividad), botón pausar/reactivar (solo
  admin, pide motivo), actividad del agente (`GET /gov/agents/{id}/activity`).
- **Registro de agentes**: formulario (nombre, sistema, área, encargado y
  correo, modelos, presupuesto + periodo, rpm/tpm, descripción) → diálogo que
  muestra la key **una sola vez** con botón copiar + guía de conexión
  (`connection.python/java/curl` que devuelve la API). Acciones: regenerar
  key, editar límites (`PATCH`), dar de baja (`DELETE`), crear sistema nuevo.
- **Notificaciones**: campana en el header con contador
  (`GET /gov/notifications`, sondeo cada 30 s), bandeja, marcar leídas.
- **Laboratorio**: elegir Talentia o AgentFactory, escribir la entrada, ver el
  resultado nodo por nodo (`POST /lab/runs/{sistema}`).

**Aceptación**: todo se opera desde TokenIO; un viewer ve pero no puede pausar
ni crear keys.

---

## Fase 8 — Modo servidor en red local + documentación

- Gateway: `GATEWAY_HOST=0.0.0.0` en `services/gateway/.env`; en governance
  `GATEWAY_PUBLIC_URL=http://<ip-de-tu-pc>:4000` (es lo que aparece en la guía
  de conexión). Abrir el puerto 4000 en el firewall de tu máquina.
- Guía para compañeros (Python/LangChain y Java/Quarkus con LangChain4j:
  `quarkus.langchain4j.openai.base-url=http://<ip>:4000/v1`, `api-key=<virtual key>`,
  `model-name=llama-local`).
- `scripts/dev-up.ps1`: levanta en orden Postgres+gateway, governance,
  agent-lab, backend y frontend.
- `docker-compose.yml` (gateway + postgres + governance + agent-lab) para tu
  máquina/servidor.
- README de `services/` en español.
- Notas de la Opción 1: agent-lab como runtime alojado expuesto a clientes;
  Agent Gateway / MCP Gateway de LiteLLM.
- Luego: agregar API keys reales (descomentar `claude-sonnet` en
  `config.yaml`, keys en `.env`, grupo `cloud-models`).

**Aceptación (prueba final)**: desde otra PC de la red, un compañero usa su
virtual key de `desarrollo`; su consumo aparece en TokenIO y se le puede pausar.
