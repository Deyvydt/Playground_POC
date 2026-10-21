---
name: sdd-specs
description: Mantiene los specs de TokenIO (spec.md, plan.md, tasks.md, data-model, contracts, quickstart, features) sincronizados con el código, siguiendo SDD estilo GitHub Spec Kit. Usar al empezar una funcionalidad nueva, antes de cambiar el alcance, después de cualquier cambio de comportamiento, endpoints, modelos de datos, permisos o configuración, y cuando el usuario pida "actualizar los specs", "documentar el cambio" o "crear un spec".
---

# Specs siempre actualizados (SDD)

En este repositorio el spec es la fuente de verdad: primero se describe el
comportamiento, luego se prueba y al final se implementa. Un cambio de código
sin su spec actualizado no está terminado.

## 1. Mapa de los specs

| Archivo | Qué contiene | Se actualiza cuando... |
|---|---|---|
| `.specify/memory/constitution.md` | Principios no negociables (versionada) | Cambia un principio o una restricción global. Sube la versión y anota el cambio arriba. |
| `specs/NNN-<nombre>/spec.md` | Qué y por qué: historias `US-N`, criterios numerados (`CA-N.M`), fuera de alcance | Cambia lo que el sistema hace o para quién. |
| `specs/NNN-<nombre>/plan.md` | Cómo: arquitectura, decisiones, dependencias | Cambia una decisión técnica o un componente. |
| `specs/NNN-<nombre>/tasks.md` | Tareas por fase con `[x]`/`[ ]`, defectos y hallazgos | Se termina, agrega o descarta trabajo. |
| `specs/NNN-<nombre>/data-model.md` | Entidades y campos | Cambia un modelo SQLModel o una tabla. |
| `specs/NNN-<nombre>/contracts/api.md` | Rutas, cuerpos, códigos y permisos | Cambia un endpoint o sus respuestas. |
| `specs/NNN-<nombre>/quickstart.md` | Cómo levantar y demostrar | Cambia un paso de instalación, una variable o un comando. |
| `specs/NNN-<nombre>/features/*.feature` | Criterios ejecutables (Gherkin) | Cambia o se agrega un criterio (skill `sdd-pruebas`). |
| `AGENTS.md` | Guía para agentes de IA | Cambia la arquitectura, una convención o cómo se prueba. |

Specs actuales: `001-agent-playground` (plataforma), `002-llm-gateway` (gobierno
de LLMs), `003-test-automation` (pruebas).

## 2. Procedimiento

1. **Ubica el spec** dueño del cambio (`grep -rn` en `specs/`). Si es una
   funcionalidad nueva con usuarios o alcance propios, crea `specs/NNN-<nombre>/`
   con el siguiente número libre y copia la estructura de `spec.md`, `plan.md` y
   `tasks.md` de un spec existente (encabezado con Feature branch, Creado, Estado,
   Entrada).
2. **Escribe o ajusta las historias** en `spec.md`:
   `### US-N — Título (Prioridad: Pn)`, "Como... quiero... para..." y criterios
   numerados. Agrega criterios al final, nunca renumeres los existentes: los tags
   `@CA-N.M` de los `.feature` dependen de esa numeración.
3. **Revisa la constitución**: si el cambio choca con un principio (privacidad,
   independencia de proveedores, observabilidad, UX minimalista, simplicidad de
   alcance), detente y pregunta antes de seguir.
4. **Actualiza plan, data-model y contracts** según la tabla anterior.
5. **Haz ejecutables los criterios** con la skill `sdd-pruebas` o el agente
   `disenador-pruebas`.
6. **Actualiza `tasks.md`**: marca lo hecho, agrega lo pendiente, registra
   defectos corregidos y hallazgos abiertos.
7. **Actualiza el estado** en el encabezado de `spec.md` si cambió (por ejemplo,
   de "Borrador" a "Implementada").
8. **Verifica**: `python scripts/run-tests.py` pasa y la matriz de trazabilidad del
   reporte no muestra historias "Sin escenarios".

## 3. Lista de control antes de dar un cambio por terminado

- [ ] El comportamiento nuevo o cambiado está en `spec.md` como criterio numerado.
- [ ] Endpoints, códigos y permisos coinciden con `contracts/api.md`.
- [ ] Campos nuevos están en `data-model.md`.
- [ ] Variables de entorno o comandos nuevos están en `quickstart.md`, el
  `.env.example` correspondiente y, si aplica, `services/README.md`.
- [ ] Cada criterio nuevo tiene escenario o prueba técnica, o está declarado como
  manual en la sección 7 de `specs/003-test-automation/plan.md`.
- [ ] `tasks.md` refleja lo hecho y lo pendiente.
- [ ] `AGENTS.md` sigue siendo correcto.

## 4. Estilo

- Español claro, frases cortas, sin relleno. Los specs los leen personas de
  negocio y agentes de IA.
- Qué y por qué en `spec.md`; cómo en `plan.md`. No mezclar.
- Rutas de archivo entre comillas invertidas; fechas en formato AAAA-MM-DD.
