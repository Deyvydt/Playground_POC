---
name: levantar-tokenio
description: Instala y levanta TokenIO completo (gateway LiteLLM, governance, backend, agent-lab, frontend) en una máquina Windows sin Docker, con modelos locales de Ollama y trazas opcionales en Langfuse Cloud, y verifica que todo funcione. Usar cuando pidan "levantar TokenIO", "instalar en otra máquina", "preparar el ambiente" o "correr la fase A".
---

# Levantar TokenIO en Windows (sin Docker)

Orden: prerrequisitos → entornos → `.env` → `dev-up.ps1` → verificación.
Validado el 2026-10-22 (`specs/004-system-integration/evidencias/2026-10-22/resultados.md`).

## Reglas de secretos (no negociables)

- **El agente nunca genera, lee, imprime ni pide valores secretos.** El usuario los
  genera en su terminal y los pega en los `.env`. Nada de keys en el chat ni en capturas.
- Para revisar los `.env` usar solo `check_env.py` (abajo): no muestra valores.
- Cada máquina usa sus propios secretos (no copiar los `.env` de otra PC).

## 1. Prerrequisitos

Python 3.11+, Node 20+, Ollama corriendo. Verificar con `python --version`,
`node --version`, `ollama list`.

El gateway usa los nombres de `services/gateway/config.yaml`: `llama-3.2-3b-it` y
`gte-large`. Si la máquina tiene otros nombres, crear alias **sin tocar config.yaml**
(no duplica espacio; se corre desde cualquier carpeta):

```powershell
ollama cp llama3.2:3b llama-3.2-3b-it
ollama cp nomic-embed-text gte-large
```

## 2. Entornos (lo puede hacer el agente)

Desde la raíz del repo, para `services\gateway`, `services\governance`,
`services\agent-lab` y `backend`:

```powershell
python -m venv <dir>\.venv
<dir>\.venv\Scripts\python -m pip install -r <dir>\requirements.txt
```

Y `npm install` en `frontend`.

## 3. Archivos `.env` (lo hace el usuario, guiado)

1. Copiar las plantillas: `copy <dir>\.env.example <dir>\.env` en los 4 servicios.
   Los `.env.example` se quedan (son la plantilla versionada); los `.env` están en `.gitignore`.
2. El usuario genera los secretos en **su** terminal:

```powershell
services\gateway\.venv\Scripts\python -c "import secrets as s; from cryptography.fernet import Fernet as F; print('MASTER_KEY =', 'sk-'+s.token_urlsafe(24)); print('SALT_KEY   =', 'sk-'+s.token_urlsafe(24)); print('SERVICE_TOK=', s.token_urlsafe(24)); print('WEBHOOK_TOK=', s.token_urlsafe(24)); print('SECRET_KEY =', s.token_urlsafe(32)); print('FERNET_GW  =', F.generate_key().decode()); print('FERNET_LAB =', F.generate_key().decode())"
```

3. Dónde va cada valor (un mismo valor en varios archivos = confianza entre servicios):

| Valor | Archivo → variable |
|---|---|
| MASTER_KEY | gateway `LITELLM_MASTER_KEY` y governance `LITELLM_MASTER_KEY` |
| SALT_KEY | gateway `LITELLM_SALT_KEY` (no cambiarla después de crear keys) |
| SERVICE_TOK | governance, agent-lab y backend `SERVICE_TOKEN` |
| WEBHOOK_TOK | governance `WEBHOOK_TOKEN` y al final de `WEBHOOK_URL` del gateway (`?token=`) |
| SECRET_KEY | backend `SECRET_KEY` |
| FERNET_GW | backend `GATEWAY_FERNET_KEY` |
| FERNET_LAB | agent-lab `LAB_FERNET_KEY` |

4. En backend descomentar `LLM_GATEWAY_URL` y `GOVERNANCE_URL` (sin ellas no hay
   gateway ni trazas).
5. Langfuse (opcional): en gateway `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` y
   **`LANGFUSE_HOST`** (Langfuse muestra `LANGFUSE_BASE_URL`; este proyecto lee `LANGFUSE_HOST`).
   Keys en https://cloud.langfuse.com → proyecto → Settings → API Keys.
6. Validar:

```powershell
services\gateway\.venv\Scripts\python .claude\skills\levantar-tokenio\check_env.py
```

## 4. Levantar

```powershell
.\scripts\dev-up.ps1
```

Abre una ventana por servicio y, en orden: gateway (+Postgres) → áreas (`bootstrap.py`)
→ governance → backend → agent-lab (+`provision.py`) → frontend. La primera vez el
gateway tarda hasta ~5 min. Debe terminar en `Listo: http://localhost:5173` y la
ventana del gateway debe decir `Trazas en Langfuse: activadas` si se configuró.

**No presionar Ctrl+C en las ventanas de servicio** (detiene el servicio; para copiar:
seleccionar y clic derecho). Para reiniciar uno, `Ctrl+C` en su ventana y volver a
correr su comando (están en `scripts/dev-up.ps1`; p. ej. backend:
`.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000`).

## 5. Verificación (A-00)

```powershell
foreach ($u in 'http://127.0.0.1:8000/api/health','http://127.0.0.1:8100/gov/health','http://127.0.0.1:8200/lab/health') { (Invoke-WebRequest $u -UseBasicParsing).Content }
cd services\gateway; .venv\Scripts\python verify_gateway.py; cd ..\..
```

Esperado: tres `ok` y `4/4 casos correctos`. Luego en http://localhost:5173
(`ana.rios@tcs.com` / `Tcs2026!`): Agentes → Soporte TI → "¿Estado del ticket TCS-4471?"
→ la traza muestra `consultar_ticket_interno`; en Langfuse → Rastreo aparece la traza
con tags `agente`, `área`, `sistema` y el texto `redacted-by-litellm`.

## Problemas conocidos

| Síntoma | Causa | Solución |
|---|---|---|
| El gateway muestra `KeyboardInterrupt` y Postgres `fast shutdown request` segundos después de arrancar | LiteLLM usa `os.kill(pid, 0)`, que en Windows es Ctrl+C (D002) | Ya corregido: `start.py` arranca LiteLLM vía `win_compat.py`. No arrancar `litellm` directo |
| Asesor de Onboarding responde "no tengo información" | El manual se sembró antes de crear las áreas (D001) | Ya corregido en `dev-up.ps1`. En una base vieja: reiniciar el backend |
| Error 404 "El equipo no existe" en Langfuse | Faltó `bootstrap.py` | `dev-up.ps1` lo corre; manual: `services\gateway\.venv\Scripts\python services\gateway\bootstrap.py` |
| Login o tablas raras tras actualizar el repo | `backend/data/playground.db` de una versión anterior | Renombrarla (backup) y reiniciar el backend: se crea y siembra una nueva |
| Los costos se ven $0.00 | Costo interno ficticio de modelos locales, redondeado | Normal; Langfuse muestra el valor exacto |
