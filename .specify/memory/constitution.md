<!--
Sync Impact Report
- Version: (none) -> 1.0.0
- Ratified: 2026-09-30
- Principles added: I. Privacidad y Localidad de Datos, II. Independencia de Proveedores,
  III. Observabilidad y Trazabilidad, IV. UX Minimalista y Accesible, V. Simplicidad de Alcance (POC)
- Templates reviewed: specs/001-agent-playground/{spec,plan,tasks}.md (aligned, no changes required)
-->

# Constitución — TCS Agent Playground

## Propósito

Este documento fija los principios no negociables para el diseño y desarrollo del
prototipo (POC) "TCS Agent Playground": un entorno propio para crear, probar y
administrar agentes de IA internos de Tata Consultancy Services. Sirve como
referencia para cualquier decisión de producto o técnica posterior.

## Principios

### I. Privacidad y Localidad de Datos (NO NEGOCIABLE)
El sistema DEBE poder operar con modelos ejecutados localmente (vía Ollama) para
que ningún prompt, documento interno o conversación salga de la infraestructura
controlada por TCS. Cualquier integración futura con un proveedor externo de LLM
DEBE ser opcional y explícita, nunca el único camino disponible.
**Razón**: es el argumento central de negocio frente a un playground público —
confidencialidad de datos de clientes y de propiedad intelectual interna.

### II. Independencia de Proveedores
La capa que invoca modelos DEBE estar aislada detrás de un cliente/adaptador
único (`ollama_client`), de forma que agregar o cambiar un proveedor de modelo
sea un cambio localizado, no una reescritura. Un agente DEBE poder declarar su
modelo de forma independiente de los demás.
**Razón**: evita el "vendor lock-in" y permite reaccionar a cambios de precio o
políticas de terceros con mínima fricción.

### III. Observabilidad y Trazabilidad
Toda interacción con un agente (turno de chat o paso de un flujo multi-agente)
DEBE producir una traza legible por humanos: prompt de sistema usado, contexto
recuperado (RAG), herramientas invocadas con sus argumentos/resultados, y la
respuesta final — además de latencia y conteo de tokens.
**Razón**: sin trazabilidad no hay confianza operativa ni forma de depurar o
auditar el comportamiento de un agente antes de llevarlo a producción.

### IV. UX Minimalista y Accesible
La interfaz DEBE seguir una paleta reducida (blanco, negro/grises y el acento de
marca de TCS), tipografía consistente, estados vacíos y de carga explícitos, y
contraste/accesibilidad de color validados (ninguna serie de datos DEBE depender
únicamente del color). Cada pantalla DEBE responder a la pregunta "¿para qué
sirve esto y qué beneficio de negocio demuestra?".
**Razón**: el público objetivo del POC incluye a personas no técnicas (gerencia);
la claridad visual es tan importante como la funcionalidad.

### V. Simplicidad de Alcance (POC)
El sistema DEBE resolver el flujo completo de las cuatro áreas funcionales
(creación de agentes, conocimiento/RAG, pruebas en playground, monitoreo/RBAC)
con la implementación más simple que lo demuestre honestamente. Autenticación,
multi-tenencia real, escalado horizontal y integraciones corporativas (SSO/AD,
Ultimatix, etc.) quedan fuera de alcance y se documentan como trabajo futuro,
no se simulan con complejidad innecesaria.
**Razón**: es un prototipo para decidir si se invierte en una versión productiva,
no el sistema final; sobre-construir retrasa la demo sin agregar valor de decisión.

## Restricciones Técnicas

- Backend: Python + FastAPI + SQLite (sin dependencias de infraestructura externa).
- Frontend: React + Vite + Tailwind CSS (sin frameworks pesados innecesarios).
- Motor de modelos: Ollama, ejecutándose en `localhost:11434`.
- Persistencia de embeddings: SQLite (JSON) + similitud coseno en memoria — sin
  motor de base de datos vectorial dedicado, dado el volumen de datos del POC.

## Gobernanza

Esta constitución prevalece sobre cualquier práctica de desarrollo en conflicto
dentro de este repositorio. Toda enmienda requiere: (1) registrar el cambio en el
"Sync Impact Report" de este archivo, (2) actualizar el número de versión según
semver (MAYOR: retiro/redefinición incompatible de un principio; MENOR: nuevo
principio o expansión material; PATCH: aclaración de redacción), y (3) revisar
que `specs/*/plan.md` siga siendo consistente.

**Versión**: 1.0.0 | **Ratificada**: 2026-09-30 | **Última enmienda**: 2026-09-30
