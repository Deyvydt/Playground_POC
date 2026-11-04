# Guía para la oficina — conectar TalentIA y agentIA_v2 a TokenIO con GenAI Lab

**Para Claude Code en otra PC:** lee esto primero. Es el estado al 2026-11-04 y los
pasos que faltan. Hablar con el usuario en español, respuestas cortas, y dejarle
hacer los pasos clave (crear keys en Gobierno) para que aprenda.

## Estado al 2026-11-04 (probado en casa con modelos locales)

| Prueba | Resultado |
|---|---|
| Agente de TalentIA (evaluador de CV) llama al LLM vía gateway | ✅ tokens, costo y latencia visibles en Gobierno |
| Pausar el agente en TokenIO | ✅ el gateway responde 401, 0 tokens consumidos |
| Reactivar | ✅ vuelve a responder |
| GenAI Lab de TCS (keys reales) | ⏳ **solo accesible desde la red de TCS**; desde casa responde `RBAC: access denied` a cualquier key |
| agentIA_v2 | ⏳ sin probar (solo configuración preparada, abajo) |

Detalle: `evidencias/2026-11-04/resultados.md`.

**Qué es qué:** TokenIO = gateway LiteLLM (:4000) + governance (:8100) + backend (:8000)
+ frontend (:5173). Los números de Gobierno salen de la base de LiteLLM, **no** de
Langfuse. Langfuse es opcional, solo para ver trazas paso a paso (sin texto de prompts).

---

## 1. Levantar TokenIO (≈ 5 min si ya hay .venv)

Usar la skill `levantar-tokenio` (o `services/README.md`). Resumen:

```powershell
cd Playground_POC
.\scripts\dev-up.ps1        # el PRIMER arranque del gateway tarda hasta 10 min (Prisma); luego ~20 s
```

Los `.env` **no están en git**: crearlos desde `.env.example` en `services/gateway`,
`services/governance`, `services/agent-lab` y `backend`. Login: `ana.rios@tcs.com` / `Tcs2026!`.

## 2. Validar las keys de GenAI Lab (en la red de TCS)

1. En `services/gateway/.env` pegar las keys del Excel `Peru.xlsx` (copiar/pegar, no
   transcribir: se confunden I/l y O/0):
   ```
   GENAILAB_API_BASE=https://genailab.tcs.in/v1
   GENAILAB_API_KEY_1=sk-...
   ...
   GENAILAB_API_KEY_6=sk-...
   ```
2. Correr:
   ```powershell
   cd services\gateway
   .venv\Scripts\python probar_genailab.py
   ```
   Lista los modelos de cada key, prueba los 3 mejores con 5 tokens y dice
   **"Mejor modelo que responde: X"**.
3. En `services/gateway/config.yaml` está el bloque comentado **"GenAI Lab de TCS"**:
   descomentar, poner `openai/<X>`, un bloque por key que funcionó, comentar los alias
   locales `gpt-4o-mini` y `llama-local`, y reiniciar el gateway (cerrar su ventana y
   `.\scripts\dev-up.ps1`).

**Nada más cambia.** Los clientes siguen pidiendo `gpt-4o-mini` / `llama-local`; el
gateway decide a qué proveedor va.

## 3. Crear una virtual key por agente (lo hace el usuario)

TokenIO → **Gobierno → Registrar agente**. La key se muestra una sola vez.

| Agente | Área | Para |
|---|---|---|
| `talentia-evaluador` | RR.HH. | TalentIA |
| `agentia-razonamiento` | Desarrollo | agentIA_v2 |
| `agentia-codigo` | Desarrollo | agentIA_v2 |

## 4. Qué deben cambiar los encargados de cada sistema

**Ningún cambio de código, solo su `.env`.** En otra PC, `127.0.0.1` → IP de la PC de
TokenIO (y ver "Modo servidor en la red local" en `services/README.md`: `GATEWAY_HOST=0.0.0.0`
y abrir el puerto 4000 en el firewall).

### TalentIA (`TalentIA/.env`)
```
TALENTIA_LLM_PROVIDER=openai
TALENTIA_LLM_MODEL=gpt-4o-mini
TALENTIA_OPENAI_BASE_URL=http://127.0.0.1:4000/v1
OPENAI_API_KEY=<key de talentia-evaluador>
```
- Usa el endpoint `/v1/responses` de OpenAI; el gateway lo soporta (probado).
- Proveedor, modelo y key se guardan en su base **la primera vez que arranca**. Si su base
  ya existe, cambiarlos en su pantalla **Admin IA**.
- Si el LLM falla (agente pausado), TalentIA **no muestra error**: evalúa sin IA y lo anota
  en auditoría (`fallback_ia`). Para comprobar la pausa, mirar Gobierno (fila "rechazada", 0 tokens).
  Si quieren un aviso visible, es un cambio de ellos.

Levantarlo en esta PC (su puerto 8000 choca con TokenIO, usar 8300):
```powershell
cd TalentIA
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e ".[graph]" tzdata python-docx   # tzdata: Windows no trae zonas horarias
# .env: copiar .env.example + las 4 líneas de arriba + TALENTIA_SESSION_SECRET (aleatorio),
#       TALENTIA_ADMIN_EMAIL=admin@talentia.local, TALENTIA_ADMIN_PASSWORD=TalentIA-Demo-2026!
.\scripts\migrate.ps1
.venv\Scripts\python scripts\seed_greenfield.py          # 3 convocatorias + 25 candidatos de demo
$env:PYTHONPATH="$PWD\src"; .venv\Scripts\python -m uvicorn talentia.main:app --port 8300
.\scripts\start_worker.ps1                                 # en otra terminal: el worker es quien llama al LLM
```
Prueba: http://127.0.0.1:8300 → Convocatorias → CONV-2026-001 → subir un CV de
`descargas_talento/02_Curriculums_25_Postulantes/` → ~30 s → ver la fila en Gobierno.

### agentIA_v2 (`agentIA_v2/.env`)
```
REASONING_LLM_PROVIDER=local
REASONING_LLM_MODEL=llama-local
REASONING_LLM_ENDPOINT=http://127.0.0.1:4000
REASONING_LLM_API_KEY=<key de agentia-razonamiento>
CODEGEN_LLM_PROVIDER=local
CODEGEN_LLM_MODEL=llama-local
CODEGEN_LLM_ENDPOINT=http://127.0.0.1:4000
CODEGEN_LLM_API_KEY=<key de agentia-codigo>
CODING_LLM_PROVIDER=local          # su .env.example usa CODING_, el código lee CODEGEN_: poner ambos
CODING_LLM_MODEL=llama-local
CODING_LLM_ENDPOINT=http://127.0.0.1:4000
CODING_LLM_API_KEY=<key de agentia-codigo>
LLM_PROVIDER=local
LLM_MODEL=llama-local
LOCAL_LLM_ENDPOINT=http://127.0.0.1:4000
LOCAL_LLM_ALLOWED_HOSTS=<ip de TokenIO, si no es 127.0.0.1>
```
- Proveedor `local` porque su política exige HTTPS para proveedores remotos; `local`
  permite `http` a hosts de `LOCAL_LLM_ALLOWED_HOSTS`.
- Su orquestador también usa el puerto 8000: arrancar con `set PORT=8010` antes de `start.bat`.
- **A verificar:** con proveedor `local`, `build_llm_client` **no** toma la key del entorno
  (`libs/agentia_runtime/llm/factory.py`, `resolve_llm_settings`). Los caminos que pasan por
  `build_reasoning_llm_client` / `build_coding_llm_client` sí la llevan; si alguna llamada
  sale sin key, el gateway responde 401 → ese camino necesita pasar `api_key` (cambio de ellos).

## 5. Prueba final (al menos un agente por sistema)

1. Ejecutar el agente en el otro sistema → aparece una fila **Correcta** con tokens en Gobierno.
2. Pausar el agente en Gobierno → su siguiente llamada da **401** (fila rechazada, 0 tokens).
3. Reactivar → vuelve a funcionar.
4. Guardar capturas en `evidencias/<fecha>/`.

Verificar por API (sin mostrar la master key):
```bash
K=$(grep '^LITELLM_MASTER_KEY=' services/gateway/.env | cut -d= -f2-)
curl -s "http://127.0.0.1:4000/spend/logs?api_key=<virtual key>" -H "Authorization: Bearer $K"
```

## Pendiente después

- Frontend de TokenIO más minimalista con la skill **impeccable** (hoy está recargado y repite
  datos en varias pantallas).
