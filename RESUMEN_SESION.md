# Resumen de la sesión — Gobierno de LLMs en TokenIO (2026-10-14, actualizado 2026-10-16)

Contexto para retomar el trabajo en otra máquina o con otro asistente.
Lo pendiente está en `FASES_PENDIENTES.md`.

## Quién y cómo trabajar
- David, ingeniero de software/IA en formación. Prefiere respuestas cortas y,
  al usar términos técnicos/siglas/comandos nuevos, una explicación en español
  de qué significan y para qué sirven (1-2 líneas).
- Trabajo por fases, un commit por paso, resumen corto al terminar cada fase y
  esperar su OK. No modificar código existente sin avisar antes.
- Commits con la identidad `Deyvydt <91276766+Deyvydt@users.noreply.github.com>`
  (configurada solo en este repo). Rama: `claude/sweet-hamilton-yklnc3`.
- Verificar en la documentación oficial (LiteLLM, Langfuse, LangGraph) antes de
  escribir configuración: la sintaxis cambia entre versiones.

## Qué era TokenIO antes de esta sesión
- Monolito en capas: FastAPI (`backend/`, :8000, SQLite) + React/Vite
  (`frontend/`, :5173). Un único adaptador a Ollama (`backend/app/ollama_client.py`).
- 6 agentes = filas en la tabla `Agent` (`backend/app/seed.py`), todos ejecutados
  por un solo motor `orchestrator.run_agent_turn` (RAG → LLM → tools → traza).
  Orquestación multi-agente = cadena lineal A→B→C. Sin LangChain/LangGraph.
- Login propio (PBKDF2 + token HMAC), roles admin/developer/viewer.
  Usuarios demo: ana.rios@tcs.com (admin), carlos.vega@tcs.com (developer),
  lucia.soto@tcs.com (viewer); contraseña `Tcs2026!`.

## El problema y el objetivo
- Las áreas **RR.HH. (sistema Talentia)** y **Desarrollo (sistema AgentFactory,
  Java/Quarkus)** tienen agentes que usan API keys reales de proveedores sin
  control de gasto ni visibilidad.
- TokenIO pasa a ser el **AI Gateway + plano de control**: cada agente recibe una
  **virtual key** emitida por TokenIO (nunca la key real). TokenIO aplica
  modelos permitidos, presupuestos y límites, puede pausar agentes (kill
  switch, manual y automático) y muestra consumo y avisos.
- **Opción 2 (en curso)**: los agentes corren en los sistemas cliente; solo
  cambian URL base y key. **Opción 1 (futuro)**: agentes alojados en TokenIO e
  invocados por API; no bloquearla.
- Prueba final: la PC de David como servidor en la red local; compañeros usan
  virtual keys desde sus agentes reales. Antes: probar con agentes LangGraph
  propios (Talentia/AgentFactory simulados) y con el modelo local; después con
  API keys reales.

## Decisiones tomadas
| Tema | Decisión |
|---|---|
| Gateway | LiteLLM Proxy (open source) |
| BD del gateway | Postgres obligatorio (SQLite no sirve para keys/budgets). Sin Docker ni admin en la PC de TCS → `pgserver` (Postgres embebido vía pip), puerto fijo 5433 |
| Docker | No en la PC de TCS. `docker-compose.yml` queda para la máquina personal |
| Trazas | Langfuse Cloud con `turn_off_message_logging` (sin texto). Self-hosted requiere Docker → después |
| Modelos | Solo Ollama local por ahora: alias `llama-local` y `embed-local`, costo interno > 0 (con 0 no se aplica presupuesto). Nube después con placeholders listos |
| Áreas (teams) | `rrhh` (Talentia), `desarrollo` (AgentFactory), `plataforma` (6 agentes de TokenIO) |
| Organización | "TCS" vive en governance (Organizations de LiteLLM es de pago) |
| Jerarquía | Organización → Área (team) → Sistema → Agente (virtual key) |
| Notificaciones | Dentro de TokenIO (campana). Email después |
| Kill switch | Manual (admin) + automático por presupuesto y por tasa de errores, siempre notifica |
| Arquitectura | **Microservicios**: gateway, governance, agent-lab, backend, frontend; cada uno con su proceso, puerto y base |
| Agentes de prueba | LangGraph, un nodo = un agente = una virtual key |
| Agentes existentes | Los 6 de TokenIO también pasan por el gateway |
| Registro | Módulo para dar de alta agentes: entrega la key **una sola vez** + guía de conexión; regenerar si se pierde |

## Arquitectura objetivo
```
frontend :5173  (/api → backend, /gov → governance, /lab → agent-lab)

backend TokenIO :8000 ─┐
agent-lab :8200 ───────┤ virtual key por agente · API formato OpenAI (/v1/chat/completions)
agentes externos ──────┘
                       ▼
          gateway LiteLLM :4000 ── Postgres (pgserver :5433) db "litellm"
             │ webhook de alertas de presupuesto ──► governance
             │ trazas (Fase 6) ──► Langfuse
             ▼
          Ollama :11434 (solo el gateway lo llama)

governance :8100 ── db "governance": registro, kill switch, monitor, notificaciones
```

## Lo implementado (commits en la rama)
- `647ebb7` Fase 0 — `specs/002-llm-gateway/{spec,plan,tasks}.md`, constitución 1.1.0, `.gitignore`.
- `bbd3d0f`, `0d11c4c` Fase 1 — `services/gateway/`: `start_db.py` (pgserver),
  `config.yaml`, `start.py`, `certs.py`, `requirements.txt` (litellm 1.105.1).
- `3f3e00e` Fase 2 — access group `local-models`, `bootstrap.py` (teams),
  `verify_gateway.py` (4/4 casos: válida 200, modelo no permitido 403,
  presupuesto 422, bloqueada 401).
- `fdb833d` Fase 3 — `services/governance/` (FastAPI :8100): registro de
  áreas/sistemas/agentes, key mostrada una vez (se guarda solo alias + hash
  SHA-256), pausar/reactivar (block/unblock), regenerar, dar de baja, monitor
  de auto-pausa (gasto ≥100 %, aviso ≥80 %, errores >50 % en 10 min con ≥5
  llamadas), webhook de alertas del gateway, notificaciones, auth delegada a
  `backend /api/auth/me` + `X-Service-Token` entre servicios.
  Todo probado de punta a punta (incluidos permisos por rol).
- Fase 4 (2026-10-16) — `services/agent-lab/` (FastAPI :8200, base propia
  `agentlab`): dos grafos LangGraph (Talentia con rama condicional por
  puntaje, AgentFactory con bucle de revisión de hasta 2 rondas), un nodo = un
  agente = una virtual key (8 en total, registrados por `provision.py` de
  forma idempotente), keys cifradas con Fernet en `app/secrets.py`, endpoint
  único `POST /lab/runs/{sistema}`. Probado de punta a punta en una máquina
  nueva: los dos grafos corren contra el modelo local vía gateway, el gasto
  sube por agente en `GET /gov/agents`, y pausar `revisor_codigo` en
  governance corta el grafo en ese nodo con "El agente está pausado por un
  administrador." `services/gateway/start_db.py` ahora también crea la base
  `agentlab`.
- Fase 5 (2026-10-16) — los 6 agentes de TokenIO pasan por el gateway cuando
  `backend/.env` define `LLM_GATEWAY_URL`: `ollama_client.py` gana un camino
  por gateway (`chat()`/`embed()` con `api_key` opcional, traduce la respuesta
  OpenAI al formato de Ollama) sin tocar el camino directo (Principio I).
  Nuevo `backend/app/gateway_keys.py`: cifra la virtual key de cada agente
  (Fernet, campo `Agent.gateway_key_enc`) y los da de alta en governance
  (sistema `tokenio`, área `plataforma`) al arrancar, de forma idempotente.
  `seed.py` usa el alias `llama-local` cuando el gateway está activo.
  `GET /api/models` lista los alias del gateway en ese modo. Probado de
  punta a punta: chat con tool-calling, RAG (embeddings vía `embed-local`),
  gasto visible en `plataforma`, y pausar "Soporte TI" en governance bloquea
  su chat con "El agente está pausado por un administrador."
  Nota de entorno: si la base SQLite ya existía antes de esta fase, hay que
  sumarle la columna a mano (`ALTER TABLE agent ADD COLUMN gateway_key_enc
  TEXT`) porque SQLite no migra solo.

## Problemas encontrados y soluciones (importante en la PC de TCS)
- **Ruta larga en Windows (>260 caracteres)** al instalar LiteLLM → instalar el
  `.venv` dentro de `services/<servicio>/`.
- **Inspección TLS corporativa** (`CERTIFICATE_VERIFY_FAILED`) al descargar
  Prisma → `certs.py` arma un bundle con certifi + CA de confianza de Windows y
  lo exporta en `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS`
  (sin desactivar verificación).
- **Cliente Prisma no generado** (con pip, a diferencia de Docker) →
  `start.py` corre `prisma generate` una vez por versión.
- **Codificación cp1252 en Windows** → `PYTHONUTF8=1` para subprocesos.
- **pgserver usa puerto aleatorio** → `start_db.py` arranca con `pg_ctl` en
  puerto fijo.
- `python-dotenv` debe ser ≥1.2.2 en el gateway (dependencia de LiteLLM).
- Ollama de la PC de TCS no tiene `llama3.2:3b` ni `nomic-embed-text` y no se
  pueden descargar (sin permisos en `C:\Ollama`); se usan `llama-3.2-3b-it` y
  `gte-large`.

## Datos útiles de LiteLLM verificados
- Todas las operaciones de admin aceptan el **hash** de la key (`/key/info`,
  `/key/block`, `/key/unblock`, `/key/update`, `/key/delete`); el hash es
  SHA-256 de la key y viene como `token` en la respuesta de `/key/generate`.
- El gasto se guarda en la base por lotes (~60 s); el chequeo de presupuesto es
  inmediato.
- `/spend/logs?api_key=<hash>` incluye llamadas fallidas (`status: failure`),
  también los rechazos por key bloqueada.
- `temperature: "abc"` provoca un 500 del modelo (útil para probar la auto-pausa
  por errores).
- Admin UI de LiteLLM: `http://127.0.0.1:4000/ui` (login con la master key).

## Próximo paso
Fase 6 (Langfuse). Pendiente aparte, no bloqueante: en esta máquina el puerto
8000 del backend quedó ocupado por un proceso que ni PowerShell ni el
terminal pueden ver ni matar (probablemente residuo de reinicios repetidos
del backend durante la Fase 5); se validó todo en el puerto 8001 como
alternativa. Revisar con David (Administrador de tareas) antes de levantar el
backend de nuevo en :8000. Ver `FASES_PENDIENTES.md`.
