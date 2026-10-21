"""Plugin de pytest que clasifica cada prueba y guarda su resultado en JSON para el reporte.

- Tipo: "funcional" si la prueba vive en una carpeta bdd/, "tecnica" en cualquier otra.
- Nivel: la carpeta inmediata (unit, api, contract, bdd).
- Tags de trazabilidad de los .feature (@spec-NNN, @US-N, @CA-N.M) como lista.

scripts/run-tests.py lee el JSON (--results-json) y arma el reporte consolidado.
"""
import json
import re
import time
from pathlib import Path

import pytest

try:
    from pytest_bdd.scenario import scenario_wrapper_template_registry
except ImportError:  # pytest-bdd no instalado: solo pruebas técnicas
    scenario_wrapper_template_registry = {}

LEVELS = {"unit": "unitaria", "api": "api", "contract": "contrato", "bdd": "aceptacion"}
TRACE_TAG = re.compile(r"^(spec-\d+|US-\d+|CA-[\d.]+)$")
# Técnicas de diseño de casos (markers de pytest o tags de los .feature). El contrato y los
# escenarios BDD reciben la suya automáticamente.
TECNICAS = {"particion", "limites", "tabla_decision", "transicion_estados", "propiedades",
            "ejemplos", "adivinanza_errores", "regresion"}
AUTO_TECNICA = {"contract": "propiedades", "bdd": "ejemplos"}


def pytest_addoption(parser):
    group = parser.getgroup("reporte")
    group.addoption("--results-json", default=None, help="Ruta del JSON de resultados para el reporte.")
    group.addoption("--componente", default=None, help="Nombre del componente bajo prueba.")


_CONFIG = None


def pytest_configure(config):
    global _CONFIG
    _CONFIG = config
    config._tokenio_results = {}
    config._tokenio_meta = {}


@pytest.hookimpl(tryfirst=True)
def pytest_bdd_apply_tag(tag, function):
    # Los tags de los .feature (@US-1, @CA-1.2...) se registran como markers para que pytest no los
    # trate como marcas desconocidas; así también sirven para filtrar con -m.
    if _CONFIG is not None:
        _CONFIG.addinivalue_line("markers", f"{tag}: tag de trazabilidad de un .feature")
    getattr(pytest.mark, tag)(function)
    return True


def _level(item) -> str:
    for part in reversed(Path(str(item.fspath)).parts):
        if part in LEVELS:
            return part
    return "unit"


def _scenario(item):
    return scenario_wrapper_template_registry.get(getattr(item, "function", None))


def pytest_collection_modifyitems(config, items):
    for item in items:
        level = _level(item)
        tipo = "funcional" if level == "bdd" else "tecnica"
        item.add_marker(getattr(pytest.mark, tipo))
        tags = sorted({m.name for m in item.iter_markers() if TRACE_TAG.match(m.name)})
        tecnicas = {m.name for m in item.iter_markers() if m.name in TECNICAS}
        if level in AUTO_TECNICA:
            tecnicas.add(AUTO_TECNICA[level])
        scenario = _scenario(item)
        if scenario is not None:
            title = scenario.name
            feature = scenario.feature.name
            source = Path(scenario.feature.rel_filename).as_posix()
        else:
            doc = (getattr(item, "obj", None).__doc__ or "").strip().splitlines() if getattr(item, "obj", None) else []
            title = doc[0] if doc else item.name.removeprefix("test_").replace("_", " ")
            feature = None
            source = None
        config._tokenio_meta[item.nodeid] = {
            "tipo": tipo,
            "nivel": LEVELS[level],
            "titulo": title,
            "caracteristica": feature,
            "feature_file": source,
            "tags": tags,
            "tecnicas": sorted(tecnicas),
        }


def pytest_runtest_logreport(report):
    config = pytest_runtest_logreport.config
    results = config._tokenio_results
    entry = results.setdefault(report.nodeid, {"resultado": "passed", "duracion": 0.0, "detalle": ""})
    entry["duracion"] += report.duration
    if report.when == "call" or report.outcome != "passed":
        if report.outcome == "failed":
            entry["resultado"] = "failed" if report.when == "call" else "error"
            entry["detalle"] = report.longreprtext[-4000:]
        elif report.outcome == "skipped" and entry["resultado"] == "passed":
            entry["resultado"] = "skipped"
            reason = report.longrepr[2] if isinstance(report.longrepr, tuple) else str(report.longrepr or "")
            entry["detalle"] = reason


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    pytest_runtest_logreport.config = session.config
    session.config._tokenio_started = time.time()


def pytest_sessionfinish(session, exitstatus):
    config = session.config
    path = config.getoption("--results-json")
    if not path:
        return
    tests = []
    for nodeid, meta in config._tokenio_meta.items():
        result = config._tokenio_results.get(nodeid)
        if result is None:
            continue  # deseleccionada con -m
        tests.append({"id": nodeid, **meta, **result})
    payload = {
        "componente": config.getoption("--componente") or Path(str(config.rootpath)).name,
        "duracion": round(time.time() - config._tokenio_started, 2),
        "exit_status": int(exitstatus),
        "pruebas": tests,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
