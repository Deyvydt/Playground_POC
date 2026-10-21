# Tareas — Integración de sistemas

Se ejecutan en computadoras físicas. Plan: `plan-de-pruebas.md`.

## Preparación
- [x] T001 Spec, plan de pruebas por fases y guía de red local
- [ ] T002 Revisar el repositorio del otro equipo: dónde llama al modelo, SDK, timeouts y manejo de errores
- [ ] T003 Acordar con el otro equipo el día de la prueba y su caso de uso real

## Fase A — Agentes de TokenIO con modelos locales
- [ ] T010 Ejecutar A-00 a A-62 y registrar evidencias en `evidencias/<fecha>/`

## Fase B — Proveedores (requiere API keys)
- [ ] T020 Configurar `claude-sonnet` (u otro) en `config.yaml` y las keys en `.env`
- [ ] T021 Ejecutar B-01 a B-08

## Fase C — Sistema de otro equipo
- [ ] T030 Red y alta del agente (C-00 a C-02)
- [ ] T031 C1 con modelo local (C-03 a C-12)
- [ ] T032 C2 con modelo en la nube

## Automatización (US-5)
- [ ] T040 Suite `tests/integration/` con `run-tests --integracion` (ver plan, sección 8)

## Hallazgos abiertos
- [ ] H002 Regenerar la key o dar de baja en Gobierno un agente del área Plataforma
  (agentes de TokenIO) deja al backend con su key anterior cifrada: el backend solo
  registra agentes sin key (`backend/app/gateway_keys.py::register_missing`), así
  que ese agente queda dando "pausado". Opciones: que el backend vuelva a pedir la
  key al recibir 401, o que Gobierno no permita regenerar keys de agentes `tokenio`.
- [ ] H003 (a verificar en B-05) Un 401 del proveedor por API key real inválida se
  traduciría como "El agente está pausado por un administrador." en backend y
  agent-lab, porque ambos interpretan cualquier 401 como pausa.
