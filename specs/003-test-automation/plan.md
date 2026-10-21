# Plan técnico y plan de pruebas: Automatización de pruebas

**Spec**: `spec.md` · **Tareas**: `tasks.md`

## 1. Estrategia

Pirámide de pruebas: muchas unitarias (rápidas y precisas), varias de API (el
contrato real con el frontend y otros servicios), contrato generado por esquema
(encuentra lo que no se nos ocurrió) y escenarios funcionales por historia de
usuario (lo que el negocio pidió).

| Tipo | Nivel | Qué verifica | Herramienta | Carpeta |
|---|---|---|---|---|
| Técnica | Unitaria | Funciones y reglas sin HTTP | pytest | `tests/<comp>/unit/` |
| Técnica | API | Endpoints, códigos HTTP, permisos | pytest + `TestClient` de FastAPI | `tests/<comp>/api/` |
| Técnica | Contrato | Ninguna solicitud válida según OpenAPI produce 5xx | Schemathesis | `tests/<comp>/contract/` |
| Funcional | Aceptación | Criterios de aceptación de cada historia | pytest-bdd + Gherkin en español | `specs/<feature>/features/` + `tests/<comp>/bdd/` |

El tipo se asigna solo, según la carpeta (`bdd/` = funcional; el resto =
técnica), por el plugin `tests/reporting_plugin.py`.

## 2. Alcance por componente

| Componente | Funcionales (`.feature`) | Técnicas |
|---|---|---|
| backend (:8000) | spec 001: agentes, chat y traza, conocimiento, flujos, consumo, sesión y usuarios, permisos por rol; spec 002 US-7 | herramientas, fragmentación, tokens, contraseñas, orquestador, metadatos de traza, API completa, contrato |
| governance (:8100) | spec 002: registro y key, presupuestos, kill switch y auto-pausa, avisos | registro, monitor, webhook, auth delegada, API, contrato |
| agent-lab (:8200) | spec 002 US-6: grafos Talentia y AgentFactory | rutas condicionales, mapeo de errores, metadatos de traza, API, contrato |

Fuera de alcance de esta iteración: frontend (E2E) y gateway LiteLLM real (ver
`spec.md`). El comportamiento del gateway que sí depende de nuestro código
(`gateway_config.py`) tiene pruebas unitarias en la suite de governance, que es
la dueña de la integración con LiteLLM.

## 3. Dobles de prueba (sin servicios externos)

| Dependencia real | Doble | Dónde |
|---|---|---|
| Ollama / gateway (chat y embeddings) | `FakeLLM`: respuestas en cola, tool-calls simulados, embeddings por bolsa de palabras (la similitud funciona de verdad) | `tests/backend/fakes.py` |
| API de administración de LiteLLM | `FakeGateway`: keys en memoria con gasto, bloqueo y registros configurables | `tests/governance/fakes.py` |
| Identidad (backend `/api/auth/me`) | `dependency_overrides` de `get_caller`: el rol viaja en el token de prueba (`Bearer rol:admin`) | `tests/governance/conftest.py`, `tests/agent-lab/conftest.py` |
| `ChatOpenAI` de LangChain | `FakeChat`: respuesta por nodo y errores del SDK de OpenAI inyectables | `tests/agent-lab/fakes.py` |
| SQLite / Postgres | SQLite temporal por ejecución; se recrea por módulo de prueba | `conftest.py` de cada componente |

## 4. Datos de prueba

- Backend: los mismos datos de demostración de `seed.py` (3 usuarios, 6 agentes,
  manual de bienvenida) con `SEED_DEMO_ACTIVITY=false` para que las métricas sean
  exactas. Tokens de sesión firmados con una clave de prueba.
- Governance: el `seed.py` del servicio (áreas `rrhh`, `desarrollo`, `plataforma`
  y sistemas `talentia`, `agentfactory`, `tokenio`).
- Agent-lab: credenciales de los 8 nodos guardadas cifradas al inicio.

## 5. Ejecución

```
python scripts/run-tests.py [--tipo funcional|tecnica|todas] [--componente ...] [--salida reports]
```

1. Por cada componente lanza `python -m pytest tests/<comp>` en un proceso propio.
2. El plugin escribe un JSON por componente con resultado, duración, tipo, nivel
   y tags de cada prueba; pytest escribe además el JUnit XML.
3. El script consolida todo en `reports/` y lee los `spec.md` para calcular la
   cobertura de historias de usuario.
4. Código de salida: 0 si no hay fallas ni errores; 1 en otro caso; 2 si una
   suite no pudo ejecutarse.

Entorno: un único virtualenv con `tests/requirements.txt` (incluye los
requirements de los tres componentes). `run-tests.ps1` / `run-tests.sh` lo crean
en `.venv-tests/` si no existe.

## 6. Criterios de entrada y salida

- **Entrada**: el spec de la funcionalidad tiene historias y criterios numerados.
- **Salida (definición de terminado)**: cada criterio nuevo tiene al menos un
  escenario; la suite completa pasa; el reporte no muestra historias "sin
  escenarios" salvo las listadas como manuales en la matriz.

## 7. Matriz de trazabilidad (resumen)

La matriz completa y actualizada la genera el reporte en cada ejecución. Las
historias que se validan manualmente por ahora:

| Spec | Historia | Motivo |
|---|---|---|
| 002 | US-1 (llamadas con virtual key al gateway) | Comportamiento de LiteLLM; se valida con `services/gateway/verify_gateway.py` contra el gateway real. |
| 002 | US-5 (trazas en Langfuse) | Requiere el gateway real; los metadatos que envían backend y agent-lab sí están automatizados. |
| 002 | US-8 (red local) | Requiere otra PC en la red. |

El script lee esta tabla: una historia listada aquí y sin escenarios aparece como
"Validación manual" en el reporte; una historia sin escenarios que no esté aquí
aparece como "Sin escenarios" (pendiente de diseñar).

Criterios sueltos que se validan manualmente o con pruebas técnicas en vez de un
escenario:

- 001 CA-3.3 (el agente admite cuando no sabe): depende del modelo real.
- 001 CA-1.3 y CA-6.1 (botones ocultos en la interfaz): parte visual; el rechazo
  del servidor sí está automatizado.
- 002 CA-3.3 (rechazo por presupuesto excedido): lo aplica LiteLLM; cubierto por
  `verify_gateway.py` y por la traducción del error 422 en las pruebas técnicas.
- 002 CA-3.4 (costo interno > 0): prueba técnica sobre `config.yaml`.
- 002 CA-5.2 (trazas sin texto en Langfuse): pruebas técnicas de los metadatos y
  de `gateway_config.py`; verificado con el gateway real el 2026-10-21.

## 8. Camino a CI / GitHub Actions

El paso del pipeline será, en cualquier proveedor:

```bash
python -m pip install -r tests/requirements.txt
python scripts/run-tests.py --salida reports
```

En GitHub Actions: publicar `reports/` como artefacto, agregar
`reports/reporte.md` a `$GITHUB_STEP_SUMMARY` y, si se desea, mostrar los JUnit
con una acción de reportes. No se agrega el workflow en esta iteración.

## 9. Convenciones

- Nombres de prueba en español que describen el comportamiento:
  `test_viewer_no_puede_crear_agentes`.
- Un `.feature` por historia o grupo de historias; escenarios con `@CA-N.M`.
- Los pasos Gherkin reutilizables de cada componente viven en `tests/<comp>/bdd/conftest.py`.
- Una prueba que falla por un defecto real del producto no se desactiva: se
  corrige el producto o se documenta en `tasks.md` como defecto abierto.
