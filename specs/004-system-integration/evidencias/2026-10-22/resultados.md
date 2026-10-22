# Resultados — Fase A (2026-10-22)

PC 1: Windows 11, Python 3.12.5, Node 20.17, Ollama 0.40.8 (`llama-3.2-3b-it` y `gte-large`
como alias de `llama3.2:3b` y `nomic-embed-text`). Langfuse Cloud (EU). Sin Docker.

| ID | Fecha | Resultado | Evidencia | Defecto | Notas |
|---|---|---|---|---|---|
| A-00 | 2026-10-22 | Pasó | capturas | D002 | Los tres health en `ok`; `verify_gateway.py` 4/4. El gateway solo arrancó tras corregir D002 |
| A-01 | 2026-10-22 | Pasó | `reports/reporte.html` | | 412/412 (56 aceptación, 135 unitarias, 174 API, 47 contrato) |
| A-10 | 2026-10-22 | Pasó | captura | | `consultar_ticket_interno` → "En progreso"; 2 rondas, 584 tokens |
| A-11 | 2026-10-22 | Pasó | Langfuse | | Trazas "Analista de Datos" en Langfuse |
| A-12 | 2026-10-22 | Pasó | captura | D001 | Falló al primer arranque (sin conocimiento); tras reiniciar el backend: 4 pasos con conocimiento, 1.25 días |
| A-13 | 2026-10-22 | Pasó | Langfuse | | Trazas "Asistente de RR.HH." en Langfuse |
| A-14 | 2026-10-22 | Pasó | Langfuse | | Flujo Analista → Redactor: trazas `flujo` de ambos agentes |
| A-15 | | Pendiente | | | |
| A-20 | 2026-10-22 | Pasó | captura | | Gobierno → Soporte TI: tokens, latencia y actividad 24 h. Costo interno ~$0.00013 (se muestra $0.00 por redondeo) |
| A-21 | 2026-10-22 | Pasó | capturas | | Pausado: "El agente está pausado por un administrador."; reactivado: responde normal. Obs.: la ficha del agente sigue mostrando "Activo" mientras está pausado en Gobierno |
| A-40 | 2026-10-22 | Pasó | capturas | | Una traza por chat con rondas anidadas; tags `agente`, `área`, `sistema`; sesión `conversación-N`; entrada/salida `redacted-by-litellm` |

## Defectos

**D001 — Primer arranque: el Asesor de Onboarding queda sin conocimiento.**
- Pasos: instalación nueva → `dev-up.ps1` → después `bootstrap.py` (como indica el script).
- Esperado: el manual de bienvenida queda indexado.
- Obtenido: el backend siembra el conocimiento al arrancar, antes de que exista el team `plataforma`; el embedding vía gateway da `404 El equipo no existe` y la siembra se omite (0 documentos). El agente responde "no tengo información".
- Corrección: `dev-up.ps1` corre `bootstrap.py` (idempotente) apenas el gateway está en línea,
  antes del backend, y `provision.py` (idempotente) tras agent-lab. En una base ya sembrada sin
  conocimiento basta con reiniciar el backend.

**D002 — Windows: el gateway se apaga a los pocos segundos de arrancar (corregido).**
- Obtenido: `KeyboardInterrupt` en el gateway y `received fast shutdown request` en Postgres sin intervención del usuario.
- Causa: LiteLLM 1.105.1 vigila el query engine de Prisma con `os.kill(pid, 0)`; en Windows la señal 0 es `CTRL_C_EVENT` y envía Ctrl+C a toda la consola (`litellm/proxy/utils.py`, `_poll_engine_proc`).
- Corrección: `services/gateway/win_compat.py` reemplaza la señal 0 por una comprobación real del proceso; `start.py` arranca LiteLLM a través de él. Verificado: el gateway sigue en línea y `verify_gateway.py` da 4/4.
