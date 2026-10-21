# Especificación de Funcionalidad: Automatización de pruebas

**Feature branch**: `003-test-automation`
**Creado**: 2026-10-21
**Estado**: Implementada — iteración 1 (pruebas funcionales y técnicas locales, listas para CI)
**Entrada**: "Automatizar las pruebas funcionales y técnicas, que ambas se ejecuten
con un solo script y generen un reporte de si pasó o no. Se llevará a un pipeline
y luego a GitHub Actions. Diseñar y planificar bien las pruebas."

## Resumen Ejecutivo

TokenIO tiene tres componentes con lógica propia (backend, governance y
agent-lab) y hasta ahora se validaba a mano. Esta funcionalidad agrega una suite
automatizada que:

- verifica **qué hace el sistema** (pruebas funcionales, escritas como escenarios
  Gherkin a partir de las historias de usuario de los specs), y
- verifica **cómo está construido** (pruebas técnicas: unitarias, de API y de
  contrato contra el esquema OpenAPI),

se ejecuta con **un solo comando**, no necesita Ollama, LiteLLM ni Postgres, y
deja un reporte legible por personas (HTML/Markdown) y por máquinas (JUnit XML y
JSON) con un código de salida apto para pipelines.

## Usuarios y Roles

| Rol | Necesidad principal |
|---|---|
| Desarrollador | Saber en minutos si su cambio rompió algo, sin levantar servicios. |
| QA / analista | Escribir criterios de aceptación como escenarios y ver qué historias están cubiertas. |
| Líder técnico | Un reporte de "pasó / no pasó" por suite y por historia de usuario. |
| Pipeline (CI) | Un comando con código de salida y reportes JUnit. |

## Historias de Usuario (por prioridad)

### US-1 — Ejecutar todas las pruebas con un solo comando (P1)
Como desarrollador, quiero ejecutar las pruebas funcionales y técnicas de todos los
componentes con un solo script, para validar un cambio sin pasos manuales.

1. `python scripts/run-tests.py` ejecuta todas las suites y termina con código 0 si
   todo pasó y 1 si algo falló.
2. Se puede filtrar por tipo (`--tipo funcional|tecnica`) y por componente
   (`--componente backend|governance|agent-lab`).
3. No requiere Ollama, LiteLLM, Postgres ni red: los servicios externos se
   reemplazan por dobles de prueba.
4. `scripts/run-tests.ps1` (Windows) y `scripts/run-tests.sh` (Linux/CI) crean el
   entorno de pruebas si no existe y luego ejecutan el script.

### US-2 — Reporte de resultados (P1)
Como líder técnico, quiero un reporte que diga claramente si las pruebas pasaron,
para decidir si un cambio está listo.

1. Se genera `reports/reporte.html` con el veredicto global, el detalle por
   componente y tipo, y el error de cada prueba fallida.
2. Se genera `reports/reporte.md` (apto para el resumen de un job de GitHub Actions)
   y `reports/resumen.json` (para otras herramientas).
3. Se conserva un JUnit XML por componente (`reports/junit-<componente>.xml`).

### US-3 — Escenarios funcionales trazables a las historias de usuario (P1)
Como QA, quiero escribir los criterios de aceptación como escenarios Gherkin en
español, para que la especificación sea ejecutable.

1. Los `.feature` viven junto al spec que validan
   (`specs/<feature>/features/*.feature`).
2. Cada escenario lleva tags de trazabilidad: `@spec-NNN`, `@US-N` y `@CA-N.M`.
3. El reporte muestra una matriz historia → escenarios → resultado, y señala las
   historias del spec que no tienen ningún escenario.

### US-4 — Pruebas técnicas por nivel (P1)
1. **Unitarias**: lógica pura (herramientas, fragmentación de texto, firma de
   tokens, rutas de los grafos, reglas del monitor).
2. **API**: cada endpoint con sus códigos de éxito y error y los permisos por rol.
3. **Contrato**: Schemathesis genera solicitudes a partir del OpenAPI de cada
   servicio y verifica que ninguna produzca un error 5xx.

### US-5 — Diseño de pruebas asistido y repetible (P2)
Como equipo que trabaja con SDD, quiero un agente y skills que generen historias,
criterios y `.feature` a partir de los specs, y que mantengan los specs al día.

1. Agente `disenador-pruebas` (`.claude/agents/`).
2. Skills `sdd-pruebas` (diseñar y ejecutar pruebas) y `sdd-specs` (mantener specs).

### US-6 — Listo para pipeline (P2)
1. El script no es interactivo, no depende del sistema operativo y escribe solo en
   `reports/`.
2. La futura integración con GitHub Actions solo necesita instalar
   `tests/requirements.txt` y ejecutar el script (ver `plan.md`).

## Requisitos No Funcionales

- La suite completa corre en menos de 2 minutos en una laptop de desarrollo.
- Las pruebas son deterministas: sin dependencia de hora, red ni datos previos.
- Cada componente se prueba en su propio proceso (los tres usan un paquete `app`).
- Ninguna prueba toca las bases de datos reales ni los `.env` del desarrollador.

## Fuera de Alcance (esta iteración)

- Pruebas de interfaz en navegador (E2E) del frontend. El flujo de Gobierno y
  Laboratorio se validó manualmente con Playwright; automatizarlo queda para la
  fase de integración de sistemas.
- Pruebas de integración contra LiteLLM, Postgres y Ollama reales (fase de
  integración de sistemas).
- Pruebas de carga y de seguridad dinámica.
- El workflow de GitHub Actions (se agrega cuando se defina el pipeline).
