# Servicios de gobierno de LLMs

TokenIO es el punto único de acceso a los modelos: cada agente recibe una
**virtual key** con su propio presupuesto, límites y modelos permitidos, y nunca
ve la key real del proveedor. Especificación completa en `specs/002-llm-gateway/`.

```
frontend :5173  (/api → backend, /gov → governance, /lab → agent-lab)

backend TokenIO :8000 ─┐
agent-lab :8200 ───────┤ virtual key por agente · API formato OpenAI (/v1/...)
agentes externos ──────┘
                       ▼
          gateway (LiteLLM) :4000 ── Postgres :5433 (bases litellm, governance, agentlab)
             │ webhook de alertas de presupuesto ──► governance
             │ trazas (opcional) ──► Langfuse
             ▼
          Ollama :11434  (y proveedores en la nube cuando haya API keys)

governance :8100 ── registro de agentes, kill switch, monitor de auto-pausa, avisos
```

| Carpeta | Puerto | Qué hace |
|---|---|---|
| `gateway/` | 4000 | Proxy LiteLLM: autentica la virtual key, aplica presupuesto y límites, enruta al modelo, registra el gasto. |
| `governance/` | 8100 | Áreas → sistemas → agentes. Emite y regenera keys, pausa y reactiva, avisos. Lo usa la página **Gobierno**. |
| `agent-lab/` | 8200 | Dos grafos LangGraph de prueba (Talentia y AgentFactory). Un nodo = un agente = una key. Lo usa la página **Laboratorio**. |

Los tres validan la sesión de TokenIO contra el backend (`/api/auth/me`): un
solo login y los mismos roles. Pausar, registrar y emitir keys es solo para
administradores; un usuario con rol de lectura ve todo pero no puede actuar.

---

## 1. Puesta en marcha en una máquina nueva

Los `.env`, los `.venv` y los datos de Postgres (`services/.data/`) **no están en
git**. En Windows usa `.venv\Scripts\python`; en Linux/Mac, `.venv/bin/python`.

```powershell
# Gateway (LiteLLM + Postgres embebido)
cd services\gateway
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
#   LITELLM_MASTER_KEY y LITELLM_SALT_KEY: valores aleatorios que empiecen por "sk-"
#   python -c "import secrets;print('sk-'+secrets.token_urlsafe(24))"
.venv\Scripts\python start.py            # Postgres :5433 + gateway :4000 (la 1.ª vez genera el cliente Prisma)
# en otra terminal, una sola vez:
.venv\Scripts\python bootstrap.py        # crea los teams rrhh / desarrollo / plataforma
.venv\Scripts\python verify_gateway.py   # debe dar 4/4

# Governance
cd services\governance
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
#   LITELLM_MASTER_KEY = la misma del gateway
#   SERVICE_TOKEN y WEBHOOK_TOKEN = valores aleatorios
#   Copia WEBHOOK_TOKEN dentro de WEBHOOK_URL en services\gateway\.env y reinicia el gateway
.venv\Scripts\python -m uvicorn app.main:app --port 8100

# Agent lab
cd services\agent-lab
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
#   SERVICE_TOKEN = el de governance; LAB_FERNET_KEY:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
.venv\Scripts\python provision.py        # una sola vez: registra los 8 nodos en governance
.venv\Scripts\python -m uvicorn app.main:app --port 8200
```

Para que los 6 agentes de TokenIO también pasen por el gateway, descomenta en
`backend/.env` el bloque "Gobierno de LLMs" (`LLM_GATEWAY_URL`, `GOVERNANCE_URL`,
`SERVICE_TOKEN`, `GATEWAY_FERNET_KEY`). Sin esas variables el backend llama a
Ollama directo, igual que antes.

### Todo de una vez (Windows)

Con los `.venv` y `.env` ya creados:

```powershell
.\scripts\dev-up.ps1          # gateway → governance → backend → agent-lab → frontend
.\scripts\dev-up.ps1 -Lan     # además expone el frontend en la red local
.\scripts\dev-up.ps1 -SinLab  # sin agent-lab
```

Cada servicio abre su propia ventana; el script espera a que cada uno responda
antes de lanzar el siguiente.

### Notas

- **Modelos de Ollama.** `gateway/config.yaml` usa `llama-3.2-3b-it:latest` y
  `gte-large:latest`. Ajusta los `model:` a los que tengas (`ollama list`), p. ej.
  `ollama_chat/llama3.2:3b` y `ollama/nomic-embed-text`. Los alias que ven los
  clientes (`llama-local`, `embed-local`) no cambian.
- **Ruta larga en Windows.** Instala en rutas cortas: la ruta de LiteLLM supera
  los 260 caracteres en carpetas muy profundas.
- **Red con inspección TLS.** `gateway/certs.py` agrega las CA de Windows al
  bundle de certificados; fuera de esa red no estorba.

---

## 2. Trazas en Langfuse (opcional)

1. Crea un proyecto en [Langfuse Cloud](https://cloud.langfuse.com) o levanta
   Langfuse en tu máquina ([guía oficial](https://langfuse.com/self-hosting)).
2. En `gateway/.env` agrega `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` y
   `LANGFUSE_HOST`, y reinicia el gateway. Al arrancar verás
   `Trazas en Langfuse: activadas`.

No hace falta editar `config.yaml`: `gateway_config.py` genera una copia con los
callbacks cuando encuentra las keys. Se envían **solo tokens, costo, latencia y
errores**; el texto de prompts y respuestas no sale del gateway
(`turn_off_message_logging`).

Cómo se agrupan las trazas:

| Origen | Traza | Generaciones | Sesión |
|---|---|---|---|
| Chat de TokenIO | un turno (`chat · <agente>`) | cada llamada al modelo y la búsqueda en conocimiento | la conversación |
| Flujo de TokenIO | el flujo completo | cada agente del flujo | — |
| Agent lab | una ejecución del grafo (`trace_id` = `run_id`) | cada nodo | — |
| Agentes externos | lo que envíen en `metadata.trace_id` | `metadata.generation_name` | `metadata.session_id` |

Todas llevan los tags `agent:<id>`, `area:<área>` y `sistema:<sistema>` para filtrar.

---

## 3. Modo servidor en la red local

Para que tus compañeros usen el gateway desde sus PCs:

1. En `gateway/.env`: `GATEWAY_HOST=0.0.0.0` y reinicia el gateway.
2. En `governance/.env`: `GATEWAY_PUBLIC_URL=http://<ip-de-tu-pc>:4000` (es la URL
   que aparece en la guía de conexión al registrar un agente). Reinicia governance.
3. Abre el puerto 4000 en el firewall de Windows (PowerShell como administrador):
   ```powershell
   New-NetFirewallRule -DisplayName "TokenIO gateway" -Direction Inbound -Protocol TCP -LocalPort 4000 -Action Allow -Profile Private
   ```
4. Opcional, para que vean TokenIO en el navegador: `.\scripts\dev-up.ps1 -Lan` y
   abrir también el puerto 5173.

Solo el gateway necesita estar expuesto: governance, agent-lab y Postgres siguen
escuchando en `127.0.0.1`.

**Prueba final.** Registra en **Gobierno** un agente del área *Desarrollo*,
entrega la key a un compañero y pídele que llame al gateway desde su PC (abajo).
Su consumo debe aparecer en la fila del agente y, si lo pausas, su siguiente
llamada debe fallar con 401.

---

## 4. Guía para conectar un agente

Pide a un administrador que registre el agente en **Gobierno → Registrar
agente**. Recibirás una virtual key (`sk-...`) que se muestra una sola vez, y la
URL base del gateway. El modelo se pide por alias: `llama-local` (chat) o
`embed-local` (embeddings).

**Python (LangChain)**
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(base_url="http://<ip>:4000/v1", api_key="<VIRTUAL_KEY>", model="llama-local")
print(llm.invoke("Hola").content)
```

**Java (Quarkus + LangChain4j)**, en `application.properties`:
```properties
quarkus.langchain4j.openai.base-url=http://<ip>:4000/v1
quarkus.langchain4j.openai.api-key=${VIRTUAL_KEY}
quarkus.langchain4j.openai.chat-model.model-name=llama-local
```

**cURL**
```bash
curl http://<ip>:4000/v1/chat/completions \
  -H "Authorization: Bearer <VIRTUAL_KEY>" -H "Content-Type: application/json" \
  -d '{"model": "llama-local", "messages": [{"role": "user", "content": "Hola"}]}'
```

Para que tus llamadas se agrupen en Langfuse, agrega en el cuerpo
`"metadata": {"trace_id": "<id de la ejecución>", "generation_name": "<paso>"}`
(en LangChain: `llm.invoke(..., extra_body={"metadata": {...}})`).

Qué significan los errores del gateway:

| Código | Significado |
|---|---|
| 401 | Key inválida o agente pausado por un administrador |
| 422 | Presupuesto del periodo agotado |
| 429 | Límite de solicitudes o tokens por minuto superado |
| 403 | El modelo pedido no está habilitado para el agente |

---

## 5. Con Docker

`docker-compose.yml` levanta Postgres, el gateway (imagen oficial de LiteLLM),
governance y agent-lab. El backend, el frontend y Ollama siguen en tu máquina.

```bash
cd services
docker compose --env-file governance/.env up -d --build
docker compose exec gateway python /gateway/bootstrap.py   # una vez
docker compose exec agent-lab python provision.py           # una vez
```

- Usa los mismos tres `.env`; el compose reemplaza las direcciones `127.0.0.1` por
  las de la red de Docker y apunta a Ollama en `host.docker.internal`.
- El gateway queda publicado en `0.0.0.0:4000` (modo servidor). El resto, solo en
  `127.0.0.1`.
- En Linux, levanta el backend con `--host 0.0.0.0` para que governance y
  agent-lab puedan validar sesiones desde los contenedores.
- No mezcles con `start.py`: los dos usan el puerto 5433.

---

## 6. Próximos pasos

**Modelos en la nube.** Descomenta `claude-sonnet` (u otro) en
`gateway/config.yaml`, pon las API keys reales en `gateway/.env`
(`ANTHROPIC_API_KEY_1`, `ANTHROPIC_API_KEY_2`; dos deployments con el mismo
`model_name` = balanceo entre keys) y habilita el grupo `cloud-models` al
agente desde **Gobierno → Editar límites**. Asigna un costo real por token
para que el presupuesto se aplique. Con modelos en la nube conviene dejar
Langfuse sin contenido de mensajes.

**Opción 1: agentes alojados en TokenIO.** Hoy los agentes corren fuera
(Opción 2) y solo consumen el modelo vía gateway. En la Opción 1 el agente
corre dentro de TokenIO y los clientes lo invocan como un servicio:

- agent-lab ya es el prototipo: sus grafos se ejecutan del lado de TokenIO
  (`POST /lab/runs/{sistema}`) y cada nodo tiene su propia key (`runtime: hosted`).
- Para exponerlo a clientes faltaría: autenticación por key de cliente (no por
  sesión de TokenIO), un registro de grafos publicados en governance y límites
  por cliente además de por nodo.
- LiteLLM trae un *Agent Gateway* (A2A) y un *MCP Gateway* que pueden servir de
  base para publicar agentes y herramientas con el mismo control de keys y
  gasto. Revisar su documentación vigente antes de adoptarlos.
