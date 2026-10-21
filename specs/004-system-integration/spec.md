# Especificación de Funcionalidad: Integración de sistemas

**Feature branch**: `004-system-integration`
**Creado**: 2026-10-21
**Estado**: Planificada — se ejecuta en computadoras físicas (no en la nube)
**Entrada**: "Plan de pruebas primero con los agentes que tenemos y modelos locales,
luego con modelos de proveedores (API keys), y después integrando los sistemas de
otros equipos, con modelos locales y de proveedores. Cuando un agente de otro
sistema llama con su virtual key, en TokenIO se deben ver sus tokens y consumo; y
cuando lo bloqueamos, a ellos les debe salir un error."

## Resumen Ejecutivo

Las specs 001 y 002 están implementadas y la spec 003 las prueba con dobles (sin
servicios reales). Esta spec valida el sistema **de punta a punta con servicios
reales** en tres fases:

| Fase | Qué se conecta | Modelos |
|---|---|---|
| A | TokenIO completo en una PC (backend, frontend, gateway, governance, agent-lab) | Locales (Ollama) |
| B | Lo mismo, con proveedores en la nube | API keys reales (Anthropic u otros) |
| C | Un sistema de otro equipo, en otra PC de la misma red, usando una virtual key de TokenIO | C1: locales · C2: proveedores |

Documentos: `plan-de-pruebas.md` (casos, criterios de entrada/salida, riesgos) y
`guia-red-local.md` (cómo conectar dos PCs paso a paso).

## Usuarios y Roles

| Rol | Necesidad |
|---|---|
| Administrador de TokenIO | Emitir keys, ver consumo de otros sistemas, pausarlos. |
| Encargado del sistema cliente | Conectar su sistema con una URL y una key, sin manejar keys reales. |
| QA | Ejecutar el plan, registrar evidencias y defectos. |

## Historias de Usuario (por prioridad)

Cada criterio se identifica como `CA-<historia>.<número>`.

### US-1 — Validar los agentes de TokenIO con modelos locales reales (Prioridad: P1)
Como QA, quiero ejecutar los agentes, flujos y grafos de TokenIO contra Ollama a
través del gateway, para confirmar que lo probado con dobles funciona igual con
servicios reales.

1. Los 6 agentes responden por el gateway y su traza muestra los pasos reales
   (herramienta, conocimiento recuperado, llamadas al modelo).
2. El consumo de cada agente aparece en Gobierno (área Plataforma) y en Consumo.
3. Pausar un agente en Gobierno hace que su chat responda con un mensaje claro;
   reactivarlo lo restablece.
4. Superar el presupuesto, el límite por minuto o la tasa de errores produce el
   rechazo o la pausa esperados y un aviso en la campana.
5. Los grafos de Laboratorio corren nodo por nodo y cada nodo suma su gasto.
6. Si Ollama, el gateway o governance se caen, la interfaz muestra mensajes claros
   y no errores técnicos.

### US-2 — Validar con modelos de proveedores (Prioridad: P1)
Como administrador, quiero habilitar modelos de proveedores en el gateway con API
keys reales, para que los agentes los usen con el mismo control de gasto.

1. Solo las keys con el grupo `cloud-models` pueden usar modelos en la nube.
2. El gasto registrado corresponde al precio real del proveedor (diferencia ≤ 5 %
   frente a su consola).
3. El presupuesto se aplica con dinero real: con un tope pequeño, la llamada que
   lo supera es rechazada.
4. Con dos API keys del mismo modelo, el gateway reparte las llamadas entre ambas.
5. El texto de los prompts no se envía a Langfuse.

### US-3 — Conectar el sistema de otro equipo con modelos locales (Prioridad: P1)
Como encargado de un sistema cliente, quiero cambiar solo la URL base, la key y
el nombre del modelo de mi agente para usar TokenIO desde mi PC.

1. Desde la PC del cliente se alcanza el gateway por la red local
   (`http://<ip-tokenio>:4000`).
2. Cada llamada del agente del cliente aparece en Gobierno: tokens, gasto, última
   actividad y la actividad de las últimas 24 h.
3. Al pausar el agente en TokenIO, la siguiente llamada del cliente recibe 401 y
   su sistema muestra un error controlado; al reactivarlo vuelve a funcionar.
4. Presupuesto agotado (422), límite por minuto (429), modelo no permitido (403),
   key regenerada (la anterior da 401) y agente dado de baja (401) se comportan
   como dice `services/README.md`.
5. El sistema cliente no necesita ninguna API key real ni la master key.

### US-4 — Conectar el sistema de otro equipo con proveedores (Prioridad: P2)
1. Los criterios de US-3 se cumplen con un modelo `cloud-models`.
2. El gasto en dólares del cliente aparece en su área y descuenta su presupuesto.

### US-5 — Pruebas de integración repetibles (Prioridad: P2)
1. Los casos automatizables de las fases A y C quedan como una suite
   `tests/integration/` que se ejecuta con `run-tests --integracion` contra
   servicios levantados, y se salta si no están disponibles.

## Requisitos No Funcionales

- Ninguna API key real ni la master key sale de la PC de TokenIO.
- Solo el puerto del gateway (4000) se expone a la red local; el frontend (5173)
  solo si alguien más necesita ver la interfaz.
- Las evidencias (capturas, respuestas, reportes) se guardan en
  `specs/004-system-integration/evidencias/<fecha>/` sin keys ni datos personales.

## Fuera de Alcance

- Despliegue en servidores o en la nube, HTTPS y dominios.
- Pruebas de carga formales (solo una línea base de latencia).
- Cambios en el código del sistema del otro equipo más allá de URL, key, modelo y
  manejo de errores.
