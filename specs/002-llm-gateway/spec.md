# Especificación de Funcionalidad: Gobierno de LLMs (AI Gateway + plano de control)

**Feature branch**: `002-llm-gateway`
**Creado**: 2026-10-14
**Estado**: Borrador aprobado — Opción 2 en implementación
**Entrada**: "Que todo consumo de modelos (proveedores en la nube y modelos locales)
pase por un solo punto con control, supervisión y observabilidad. Los agentes de
los sistemas de la empresa no usan API keys reales, sino virtual keys emitidas por
TokenIO."

## Resumen Ejecutivo

Las áreas de RR.HH. (sistema **Talentia**) y Desarrollo (sistema **AgentFactory**)
tienen agentes que consumen API keys reales de proveedores sin control de gasto ni
visibilidad. TokenIO se convierte en el punto único de acceso a modelos: emite una
**virtual key** por agente, aplica modelos permitidos, presupuestos y límites,
permite pausar un agente (kill switch) y muestra su consumo.

- **Opción 2 (esta iteración)**: los agentes corren en los sistemas cliente; solo
  cambian la URL base y la key que usan.
- **Opción 1 (futuro)**: los agentes corren dentro de TokenIO y los clientes los
  invocan por API. Esta iteración no la implementa, pero no debe bloquearla.

## Usuarios y Roles

| Rol | Necesidad principal |
|---|---|
| Administrador | Registrar agentes, entregar virtual keys, fijar presupuestos/límites, pausar/reactivar, recibir avisos. |
| Encargado de un sistema cliente | Recibir una virtual key y la guía de conexión para su agente. |
| Desarrollador | Ver consumo y trazas; ejecutar los agentes de prueba. |
| Solo lectura | Ver el tablero sin poder pausar ni crear keys. |

## Historias de Usuario (por prioridad)

### US-1 — Consumir modelos solo con virtual key (P1)
Como encargado de un sistema, quiero apuntar mi agente a la URL de TokenIO con una
virtual key, para no manejar API keys reales del proveedor.

1. Una llamada con virtual key válida a un modelo permitido responde con normalidad.
2. Una llamada a un modelo no permitido para esa key es rechazada.
3. El cliente solo ve alias lógicos de modelos (ej. `llama-local`), nunca URLs
   internas ni keys reales.

### US-2 — Registrar un agente y entregar su virtual key (P1)
Como administrador, quiero dar de alta un agente indicando sistema, área,
encargado, modelos, presupuesto y límites, y recibir su virtual key.

1. Al guardar, la key se muestra **una sola vez** con una guía de conexión.
2. El registro guarda solo alias y hash de la key, nunca la key en claro.
3. Si la key se pierde, se puede regenerar; la anterior deja de funcionar.

### US-3 — Presupuestos y límites por área y por agente (P1)
1. Jerarquía: Organización → Área (team) → Sistema → Agente (key).
2. Cada key tiene modelos permitidos, `max_budget` + periodo y límites rpm/tpm.
3. Al exceder el presupuesto, las llamadas son rechazadas.
4. Los modelos locales tienen costo interno > 0 para que el presupuesto aplique.

### US-4 — Kill switch y auto-pausa con aviso (P1)
1. Un administrador pausa un agente: su estado cambia a `pausado` y su key queda
   bloqueada en el gateway. Reactivar revierte ambas cosas.
2. El sistema pausa automáticamente un agente si supera su presupuesto o su tasa
   de errores pasa un umbral configurable.
3. Toda pausa (manual o automática) y todo aviso de gasto genera una notificación
   visible en TokenIO.

### US-5 — Observabilidad de consumo (P2)
1. Gasto, tokens, latencia y errores por agente, sistema y área.
2. Trazas por ejecución de agente en Langfuse, sin el texto de los prompts en esta
   iteración (Langfuse Cloud).

### US-6 — Agentes de prueba LangGraph (P2)
Como desarrollador, quiero ejecutar desde TokenIO agentes que simulan Talentia y
AgentFactory, construidos como grafos LangGraph, cada nodo con su propia virtual
key, para validar el gobierno sin depender de los sistemas reales.

### US-7 — Agentes actuales de TokenIO bajo gobierno (P2)
Los 6 agentes existentes de TokenIO consumen modelos a través del gateway con sus
virtual keys (área `plataforma`), sin cambiar su comportamiento.

### US-8 — Modo servidor en red local (P3)
Compañeros en la misma red usan virtual keys contra la PC que corre TokenIO y su
consumo aparece en el tablero.

## Requisitos No Funcionales

- Las API keys reales nunca se versionan: viven en `.env` (ignorado por git).
- Arquitectura de microservicios: gateway, governance y agent-lab son procesos
  independientes con su propio puerto y base de datos, comunicados por HTTP.
- Sin Docker ni permisos de administrador para la iteración local (Postgres
  embebido vía `pgserver`); `docker-compose.yml` disponible para despliegues
  posteriores.
- Configuración del gateway en `config.yaml` versionable con placeholders.
- Scripts de verificación para: llamada válida, modelo no permitido, presupuesto
  excedido y key bloqueada.

## Fuera de Alcance (esta iteración)

- Opción 1 (agentes alojados expuestos a clientes) — solo se deja preparado.
- Notificaciones por correo, SSO, Langfuse self-hosted, despliegue en nube.
