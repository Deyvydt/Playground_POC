# Evidencias 2026-11-04 — Fase C1 en una sola PC (modelos locales)

Sistema cliente: **TalentIA** (agente evaluador de CV), en la misma PC que TokenIO.
Key: agente `talentia-evaluador` (área RR.HH.). Modelo pedido: `gpt-4o-mini`
(alias del gateway → Ollama `llama-3.2-3b-it`). Endpoint: `/v1/responses`.

Registro del gateway (`/spend/logs` de la key):

| Hora UTC | Tokens in/out | Estado | Qué fue |
|---|---|---|---|
| 13:19:36 | 28 / 10 | success | curl de verificación |
| 13:21:45 | 606 / 251 | success | CV subido por API (Diego Castro) |
| 13:27:57 | 608 / 263 | success | CV subido por la UI (Carlos Mendoza) |
| 13:31:16 | 0 / 0 | failure (401) | CV de Mariana Salazar con el agente **pausado** |
| 13:33:54 | 0 / 0 | failure (401) | reintento de evaluación, pausado |
| 13:35:12 | 0 / 0 | failure (401) | curl de verificación, pausado |

Resultado: C-03 (consumo visible en Gobierno) y C-05 (pausa → 401) **pasan** con un sistema real.

Hallazgos:
- TalentIA ante 401 no muestra error: cae a evaluación determinística y lo registra como
  `fallback_ia` en auditoría. Comportamiento de ellos, no de TokenIO.
- TalentIA en Windows necesita `tzdata` (no está en su `pyproject`).
- GenAI Lab (`genailab.tcs.in`) rechaza conexiones fuera de la red de TCS (`RBAC: access denied`).
- `dev-up.ps1` esperaba 300 s al gateway; el primer arranque (Prisma) tarda más. Corregido.
