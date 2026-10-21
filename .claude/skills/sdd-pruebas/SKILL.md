---
name: sdd-pruebas
description: Diseña, escribe y ejecuta las pruebas automatizadas de TokenIO (funcionales con Gherkin/pytest-bdd y técnicas con pytest y Schemathesis) y genera el reporte. Usar cuando el usuario pida "correr las pruebas", "ejecutar los tests", "ver el reporte", "agregar pruebas", "escribir un .feature", "criterios de aceptación", o después de cambiar código del backend, governance o agent-lab.
---

# Pruebas automatizadas de TokenIO (SDD)

Estrategia completa: `specs/003-test-automation/plan.md`. Esta skill es el
procedimiento.

## 1. Ejecutar

```bash
./scripts/run-tests.sh                 # Linux / macOS / CI
.\scripts\run-tests.ps1                # Windows (abre el reporte al terminar)
```

Opciones (se pasan a `scripts/run-tests.py`):

| Opción | Uso |
|---|---|
| `--tipo funcional` | Solo escenarios de los `.feature` |
| `--tipo tecnica` | Solo unitarias, API y contrato |
| `--componente backend` | Repetible: `backend`, `governance`, `agent-lab` |
| `--rapido` | Sin contrato (Schemathesis); útil mientras iteras |
| `--salida carpeta` | Otra carpeta de reportes (por defecto `reports/`) |

Si ya existe `.venv-tests/`, también sirve
`.venv-tests/bin/python scripts/run-tests.py ...`. Para depurar una sola prueba:
`.venv-tests/bin/python -m pytest tests/backend/api/test_api_chat.py -k inactivo -x`.
No ejecutes `pytest tests` completo: los tres componentes usan un paquete `app` y
deben correr en procesos separados.

## 2. Leer el resultado

- Código de salida: `0` pasó · `1` hubo fallas · `2` una suite no pudo ejecutarse
  (ver `reports/log-<componente>.txt`).
- `reports/reporte.html`: veredicto, por componente, por tipo y nivel, matriz de
  trazabilidad de historias y detalle de cada falla.
- `reports/reporte.md`: lo mismo en Markdown (para el resumen de un pipeline).
- `reports/junit-*.xml` y `reports/resumen.json`: para herramientas de CI.

En la matriz, "Sin escenarios" significa que una historia del spec no tiene
pruebas ni está declarada como manual: hay que diseñarlas (paso 3).

## 3. Agregar pruebas para un cambio

Para algo más que un par de pruebas, delega en el agente `disenador-pruebas`.
Si lo haces directamente:

1. **Spec primero**: el criterio debe existir y estar numerado en
   `specs/<feature>/spec.md` (skill `sdd-specs`).
2. **Escenario** en `specs/<feature>/features/<tema>.feature`, en español, con
   `@spec-NNN @US-N` en la característica y `@CA-N.M` en el escenario.
3. **Pasos**: reutiliza los de `tests/<componente>/bdd/conftest.py`; agrega los que
   falten ahí. Si el `.feature` es nuevo, vincúlalo en
   `tests/<componente>/bdd/test_aceptacion_<componente>.py` con `scenarios(...)`.
4. **Técnicas** en `tests/<componente>/unit/` (lógica pura) o `api/` (HTTP, códigos,
   permisos). Las rutas nuevas quedan cubiertas por el contrato automáticamente.
5. **Dobles**: `tests/backend/fakes.py` (`FakeLLM`), `tests/governance/fakes.py`
   (`FakeGateway`), `tests/agent-lab/fakes.py` (`FakeChatModel`). Si necesitas un
   comportamiento nuevo del servicio externo, amplía el doble; nunca llames al real.
6. Ejecuta `--componente <x> --rapido` mientras iteras y la suite completa al final.

| Dónde vive | Qué |
|---|---|
| `specs/*/features/*.feature` | Criterios de aceptación ejecutables |
| `tests/<comp>/bdd/` | Pasos Gherkin y vínculo con los `.feature` |
| `tests/<comp>/unit/`, `api/`, `contract/` | Pruebas técnicas |
| `tests/<comp>/conftest.py` | Entorno aislado (SQLite temporal, variables, dobles) |
| `tests/reporting_plugin.py` | Clasifica (tipo/nivel/tags) y guarda resultados |
| `scripts/run-tests.py` | Orquesta y genera el reporte |

## 4. Reglas

- Una prueba que falla por un defecto real no se desactiva: se corrige el
  producto con una prueba de regresión, o se registra en "Hallazgos abiertos" de
  `specs/003-test-automation/tasks.md` si requiere una decisión de producto.
- Pruebas deterministas: nada de hora real, red ni orden entre pruebas (cada
  prueba parte de una base nueva con los datos de `seed.py`).
- Nombres en español que describan el comportamiento:
  `test_viewer_no_puede_crear_agentes`.
- Un nombre de archivo de prueba no se repite dentro de un componente.

## 5. En un pipeline (GitHub Actions u otro)

```bash
python -m pip install -r tests/requirements.txt
python scripts/run-tests.py --salida reports
```

Publica `reports/` como artefacto y agrega `reports/reporte.md` al resumen del
job. El script no es interactivo y su código de salida decide el paso.
