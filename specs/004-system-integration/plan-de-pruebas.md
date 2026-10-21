# Plan de pruebas de integración

**Spec**: `spec.md` · **Guía de red**: `guia-red-local.md` · **Tareas**: `tasks.md`

## 1. Objetivo

Comprobar con servicios reales que TokenIO controla todo el consumo de modelos:
primero con sus propios agentes (modelos locales y luego de proveedores) y después
con el sistema de otro equipo conectado por la red local.

La suite automatizada (`scripts/run-tests.*`, spec 003) prueba la lógica con
dobles. Este plan prueba lo que los dobles no pueden: Ollama, LiteLLM, Postgres,
proveedores reales, la red y el sistema de otro equipo.

## 2. Ambiente

```
            Red local (mismo router / Wi-Fi, perfil "Privada")
   ┌───────────────────────────────┐        ┌─────────────────────────────┐
   │ PC 1 · TokenIO (servidor)      │        │ PC 2 · Sistema del otro      │
   │ IP ej. 192.168.1.50            │        │ equipo (cliente)             │
   │                                │  HTTP  │                              │
   │ gateway LiteLLM :4000 ◄────────┼────────┤ su agente                    │
   │ governance :8100 (solo local)  │        │  base_url=http://192.168.1.50│
   │ backend :8000 · frontend :5173 │        │           :4000/v1           │
   │ agent-lab :8200 · Postgres     │        │  api_key=<virtual key>       │
   │ Ollama :11434                  │        │  model=llama-local           │
   └───────────────────────────────┘        └─────────────────────────────┘
```

| Elemento | Requisito |
|---|---|
| PC 1 | Windows 10/11, 16 GB RAM recomendados (Ollama + 5 servicios), Python 3.11+, Node 20+, Ollama con los modelos de `services/gateway/config.yaml` |
| PC 2 | El sistema del otro equipo funcionando en su forma actual (antes de cambiarlo) |
| Red | Ambas PCs en la misma red, sin "aislamiento de clientes" (las redes de invitados suelen tenerlo) |
| Langfuse | Opcional en A y C; recomendado en B |
| Fase B | API keys reales (te las paso cuando lleguemos a esa fase), con un límite de gasto en la consola del proveedor |

## 3. Estrategia por fases

| Fase | Entrada (antes de empezar) | Salida (para pasar a la siguiente) |
|---|---|---|
| A | `run-tests` pasa; `dev-up.ps1` levanta todo; `verify_gateway.py` da 4/4 | Todos los casos A en "Pasó" o con defecto registrado y aceptado |
| B | Fase A cerrada; API keys con tope de gasto en el proveedor | Casos B pasan; costo conciliado con la consola del proveedor |
| C1 | Fase A cerrada; repositorio del otro equipo revisado; red probada (C-00) | Casos C pasan con modelo local; el otro equipo valida su flujo |
| C2 | C1 y B cerradas | Casos C repetidos con `cloud-models` |

Técnicas: transición de estados (activo → pausado → activo, key regenerada,
baja), valores límite (presupuesto justo antes y después del tope, rpm = 1),
partición de equivalencias (códigos 401/403/422/429), adivinanza de errores
(servicios caídos, red cortada) y pruebas exploratorias guiadas por el flujo real
del otro equipo.

## 4. Casos de prueba

Formato de cada caso: **ID · qué se prueba · cómo · resultado esperado**. Registra
el resultado en la sección 7.

### Fase A — Agentes de TokenIO con modelos locales

| ID | Qué se prueba | Cómo | Resultado esperado |
|---|---|---|---|
| A-00 | Preparación | `.\scripts\dev-up.ps1`; `verify_gateway.py`; abrir `/api/health`, `/gov/health`, `/lab/health` | Todo en línea; 4/4; los tres health responden `ok` |
| A-01 | Regresión base | `.\scripts\run-tests.ps1` | Veredicto PASÓ |
| A-02 | Registro automático | Arrancar el backend con `LLM_GATEWAY_URL` | Los 6 agentes aparecen en Gobierno → Plataforma |
| A-10 | Soporte TI + herramienta | Chat: "¿Estado del ticket TCS-4471?" | Traza con `consultar_ticket_interno` y "En progreso" |
| A-11 | Analista + calculadora | Chat: "¿Cuánto es (120*3)/4?" | Traza con `calculadora` = 90 |
| A-12 | Onboarding + conocimiento | Chat: "¿Cuántos días de vacaciones acumulo por mes?" | Traza con fragmentos recuperados; respuesta 1.25 días |
| A-13 | RR.HH. + fecha | Chat: "¿Qué día es hoy?" | Traza con `fecha_actual` |
| A-14 | Flujo multi-agente | Flujos: Analista → Redactor | Dos pasos en vivo; resultado del Redactor |
| A-15 | Agente inactivo | Chat con "Revisor de Contratos" (sembrado inactivo) | Mensaje "Este agente está pausado" |
| A-20 | Consumo visible | Tras A-10..A-14, abrir Gobierno y Consumo | Gasto y última actividad > 0 en los agentes usados; tokens en Consumo |
| A-21 | Kill switch | Gobierno → pausar "Soporte TI" (motivo) → chatear → reactivar → chatear | 503 "El agente está pausado por un administrador."; aviso en la campana; tras reactivar responde |
| A-22 | Presupuesto (límite) | Editar límites de "Analista de Datos": presupuesto 0.0001 → chatear 2 veces | La llamada que supera el tope da "agotó su presupuesto"; el monitor lo pausa (≤ 60 s); aviso crítico |
| A-23 | Auto-pausa por errores | 5 llamadas con su key y `"temperature": "abc"` (curl de la guía de red, sección 8) | El monitor lo pausa por tasa de errores; aviso crítico |
| A-24 | Límite por minuto | Límite de 1 solicitud/min → 2 chats seguidos | El segundo responde "límite de uso" (429) |
| A-25 | Regenerar key de un agente de TokenIO | Gobierno → regenerar la key de "Redactor de Reportes" → chatear | **Hoy falla** (ver riesgo R-05): el backend sigue usando la key anterior |
| A-30 | Laboratorio Talentia | CV fuerte y CV débil | Entrevista vs rechazo; gasto por nodo en Gobierno → RR.HH. |
| A-31 | Laboratorio AgentFactory | Requerimiento simple | Recorrido con revisión; gasto en Desarrollo |
| A-32 | Nodo pausado | Pausar `revisor_codigo` → ejecutar AgentFactory | Se detiene en ese nodo con el mensaje de pausa |
| A-40 | Langfuse (si está activo) | Ejecutar A-10 y A-31 | Una traza por chat y por grafo, tags agent/area/sistema, sin texto de prompts |
| A-50 | Línea base de latencia | 10 chats por agente | Anotar mediana y máximo por agente (primer chat incluye carga del modelo) |
| A-60 | Ollama apagado | Cerrar Ollama → chatear | Mensaje claro; indicador "Motor sin conexión" |
| A-61 | Gateway apagado | Cerrar la ventana del gateway → chatear y abrir Gobierno | "El gateway no está disponible"; Gobierno muestra datos sin gasto |
| A-62 | Governance apagado | Cerrar governance → abrir Gobierno | "El servicio de gobierno no está disponible"; el chat sigue funcionando |

### Fase B — Modelos de proveedores

Preparación (B-00): en `services/gateway/config.yaml` descomentar el bloque de
`claude-sonnet` con el id de modelo vigente del proveedor; en `.env` las keys
`ANTHROPIC_API_KEY_1` y `_2`; reiniciar el gateway. Tope de gasto bajo en la consola
del proveedor.

| ID | Qué se prueba | Cómo | Resultado esperado |
|---|---|---|---|
| B-01 | Acceso por grupo | curl con una key solo `local-models` y otra con `cloud-models` al modelo en la nube | 403 y 200 |
| B-02 | Agente de TokenIO en la nube | Habilitar `cloud-models` a "Redactor de Reportes" y cambiar su modelo a `claude-sonnet` | Responde; gasto en dólares reales en Gobierno |
| B-03 | Presupuesto real (límite) | Presupuesto 0.01 USD → chatear hasta superarlo | La llamada siguiente al tope es rechazada; pausa automática |
| B-04 | Balanceo entre keys | 20 llamadas | Ambas keys usadas (Admin UI de LiteLLM o consola del proveedor) |
| B-05 | Key del proveedor inválida | Poner una key real incorrecta en `.env` | Error controlado; **verificar el mensaje** (riesgo R-06) |
| B-06 | Herramientas con proveedor | A-10 con modelo en la nube | Tool-calling funciona igual |
| B-07 | Privacidad | Revisar Langfuse y logs del gateway | Sin texto de prompts ni respuestas |
| B-08 | Conciliación de costos | Comparar gasto de Gobierno vs consola del proveedor | Diferencia ≤ 5 % |

### Fase C — Sistema de otro equipo por la red local

C1 con `llama-local`; C2 repite C-03 a C-09 con el modelo en la nube.

| ID | Qué se prueba | Cómo | Resultado esperado |
|---|---|---|---|
| C-00 | Red | Desde PC 2: `Test-NetConnection <ip-pc1> -Port 4000` | `TcpTestSucceeded : True` |
| C-01 | Alta del agente cliente | Gobierno → Sistema nuevo (o Talentia/AgentFactory) → Registrar agente con encargado, presupuesto y límites | Key mostrada una vez; guía con la IP de la PC 1 |
| C-02 | Humo desde PC 2 | `curl http://<ip>:4000/v1/models` con la key | Lista solo los alias permitidos |
| C-03 | Flujo real del cliente | El otro equipo ejecuta su caso de uso | Funciona como antes; en Gobierno sube gasto, tokens y "última actividad"; aparece en Actividad 24 h |
| C-04 | Bloqueo (kill switch) | Pausar el agente en TokenIO → el cliente vuelve a ejecutar | Su sistema recibe 401 y muestra un error controlado (no se cae) |
| C-05 | Desbloqueo | Reactivar → ejecutar | Vuelve a funcionar sin cambiar nada en PC 2 |
| C-06 | Presupuesto | Presupuesto mínimo → ejecutar hasta superarlo | 422 en el cliente; pausa automática y aviso en TokenIO |
| C-07 | Límite por minuto | 1 solicitud/min → dos ejecuciones seguidas | 429 en la segunda |
| C-08 | Modelo no permitido | El cliente pide un alias que su key no tiene | 403 |
| C-09 | Key regenerada / baja | Regenerar → probar la key vieja; dar de baja → probar la nueva | 401 en ambos casos |
| C-10 | Varios agentes del cliente | Si su sistema tiene varios agentes, una key por agente | El gasto se atribuye a cada agente por separado |
| C-11 | Trazas del cliente | Si envían `metadata.trace_id` | Sus ejecuciones agrupadas en Langfuse |
| C-12 | Red cortada | Desconectar la PC 1 durante una ejecución | El cliente maneja el timeout sin quedarse colgado |

## 5. Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| R-01 | Firewall, red "Pública" o aislamiento de clientes en el Wi-Fi impiden C-00 | Guía de red, sección 6; usar un router propio o cable |
| R-02 | La IP de la PC 1 cambia (DHCP) | Reservar la IP en el router o actualizar `GATEWAY_PUBLIC_URL` |
| R-03 | La primera llamada a Ollama tarda (carga del modelo) y el cliente agota su timeout | Calentar el modelo antes; timeout del cliente ≥ 120 s |
| R-04 | El sistema del otro equipo usa un SDK o formato no compatible | Revisar su repositorio antes de C-01; LiteLLM acepta formato OpenAI (`/v1`) y Anthropic (`/anthropic`) |
| R-05 | Regenerar o dar de baja en Gobierno un agente de TokenIO deja al backend con una key inválida (solo registra agentes sin key) | Hallazgo H002 (`tasks.md`); hasta resolverlo, no regenerar keys del área Plataforma |
| R-06 | Un 401 del proveedor (key real inválida) se mostraría como "agente pausado" | Verificar en B-05; hallazgo H003 si se confirma |
| R-07 | Gasto real inesperado en fase B | Tope en la consola del proveedor y presupuestos bajos en TokenIO |
| R-08 | Exposición de keys | Keys solo en `.env`; nunca en capturas ni en git; la master key no sale de la PC 1 |

## 6. Orden sugerido para el día de la prueba

1. PC 1: `git pull`, `.\scripts\run-tests.ps1` (A-01).
2. PC 1: `.\scripts\dev-up.ps1`, fase A completa.
3. Revisar el repositorio del otro equipo (dónde llama al modelo, qué SDK usa).
4. Red: guía de red pasos 1 a 5 y C-00.
5. C-01 a C-12 con el otro equipo presente.
6. Fase B y C2 cuando lleguen las API keys.

## 7. Registro de resultados

Copia esta tabla en `evidencias/<fecha>/resultados.md`:

| ID | Fecha | Resultado (Pasó / Falló / Bloqueado) | Evidencia (archivo) | Defecto | Notas |
|---|---|---|---|---|---|
| A-00 | | | | | |

Un defecto se registra en `tasks.md` como `D0NN` con: pasos, esperado, obtenido y
evidencia.

## 8. Automatización posterior (US-5)

Los casos A-02, A-10..A-15, A-21, A-22, A-24, A-30..A-32 y C-02..C-09 se pueden
automatizar en `tests/integration/` con `httpx` contra los servicios levantados
(marcados con `@pytest.mark.integracion`), saltándose si `/gov/health` no
responde. Se hará después de ejecutarlos a mano una vez, para fijar los
resultados esperados con datos reales.
