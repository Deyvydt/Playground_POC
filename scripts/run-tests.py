"""Ejecuta las pruebas funcionales y técnicas de TokenIO y genera un reporte consolidado.

Uso:
    python scripts/run-tests.py                          # todo
    python scripts/run-tests.py --tipo funcional         # solo escenarios de aceptación (.feature)
    python scripts/run-tests.py --tipo tecnica --rapido  # técnicas sin pruebas de contrato
    python scripts/run-tests.py --componente governance --componente agent-lab

Salida en --salida (por defecto reports/): reporte.html, reporte.md, resumen.json,
junit-<componente>.xml y log-<componente>.txt.
Código de salida: 0 todo pasó · 1 hubo fallas o errores · 2 una suite no pudo ejecutarse.

Requiere las dependencias de tests/requirements.txt (los scripts run-tests.ps1 y
run-tests.sh las instalan en .venv-tests/ si hace falta).
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COMPONENTES = {
    "backend": "tests/backend",
    "governance": "tests/governance",
    "agent-lab": "tests/agent-lab",
}
ESTADOS = {"passed": "Pasó", "failed": "Falló", "error": "Error", "skipped": "Omitida"}
NIVELES = ["unitaria", "api", "contrato", "aceptacion"]


def parse_args():
    parser = argparse.ArgumentParser(description="Pruebas automatizadas de TokenIO")
    parser.add_argument("--tipo", choices=["todas", "funcional", "tecnica"], default="todas")
    parser.add_argument("--componente", action="append", choices=list(COMPONENTES),
                        help="Repetible. Por defecto, todos los componentes.")
    parser.add_argument("--rapido", action="store_true", help="Omite las pruebas de contrato (Schemathesis).")
    parser.add_argument("--salida", default="reports", help="Carpeta de reportes (relativa al repositorio).")
    return parser.parse_args()


# --- Ejecución ------------------------------------------------------------------------------

def run_suite(nombre: str, ruta: str, args, salida: Path) -> dict:
    resultados = salida / f"resultados-{nombre}.json"
    resultados.unlink(missing_ok=True)
    cmd = [
        sys.executable, "-m", "pytest", ruta,
        "-c", "tests/pytest.ini", "--rootdir", "tests", "-p", "no:cacheprovider", "-q",
        f"--junitxml={salida / f'junit-{nombre}.xml'}",
        f"--results-json={resultados}", f"--componente={nombre}",
    ]
    if args.tipo != "todas":
        cmd += ["-m", args.tipo]
    if args.rapido:
        cmd += ["--ignore", f"{ruta}/contract"]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    inicio = time.time()
    proc = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (salida / f"log-{nombre}.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    if resultados.exists():
        data = json.loads(resultados.read_text(encoding="utf-8"))
    else:
        data = {"componente": nombre, "pruebas": [], "exit_status": proc.returncode}
    # 5 = pytest no encontró pruebas con ese filtro: no es una falla.
    data["ejecutada"] = resultados.exists() and proc.returncode in (0, 1, 5)
    data["duracion"] = round(time.time() - inicio, 2)
    return data


# --- Trazabilidad ---------------------------------------------------------------------------

US_HEADING = re.compile(r"^###\s+(US-\d+)\s+[—-]\s+(.+?)\s*(?:\((?:Prioridad:\s*)?(P\d)\))?\s*$")
MANUAL_ROW = re.compile(r"^\|\s*(\d{3})\s*\|\s*(US-\d+)[^|]*\|\s*(.+?)\s*\|\s*$")


def historias_por_spec() -> dict:
    """Historias de usuario de cada spec que tiene carpeta features/."""
    specs = {}
    for spec_md in sorted(REPO.glob("specs/*/spec.md")):
        if not (spec_md.parent / "features").is_dir():
            continue
        numero = spec_md.parent.name[:3]
        historias = {}
        for line in spec_md.read_text(encoding="utf-8").splitlines():
            m = US_HEADING.match(line.strip())
            if m:
                historias[m.group(1)] = {"titulo": m.group(2).strip(), "prioridad": m.group(3) or ""}
        specs[numero] = {"carpeta": spec_md.parent.name, "historias": historias}
    return specs


def cobertura_manual() -> dict:
    """Historias validadas manualmente (tabla de la sección 7 de specs/003-test-automation/plan.md)."""
    plan = REPO / "specs" / "003-test-automation" / "plan.md"
    manual = {}
    if plan.exists():
        for line in plan.read_text(encoding="utf-8").splitlines():
            m = MANUAL_ROW.match(line)
            if m:
                manual[(m.group(1), m.group(2))] = m.group(3)
    return manual


def trazabilidad(pruebas: list[dict]) -> list[dict]:
    escenarios = defaultdict(list)
    for p in pruebas:
        if p["tipo"] != "funcional":
            continue
        spec = next((t.removeprefix("spec-") for t in p["tags"] if t.startswith("spec-")), None)
        for us in (t for t in p["tags"] if t.startswith("US-")):
            escenarios[(spec, us)].append(p)
    manual = cobertura_manual()
    filas = []
    for numero, spec in historias_por_spec().items():
        for us, info in spec["historias"].items():
            casos = escenarios.get((numero, us), [])
            conteo = Counter(c["resultado"] for c in casos)
            if casos:
                estado = "passed" if conteo["passed"] == len(casos) else ("failed" if conteo["failed"] or conteo["error"] else "skipped")
            else:
                estado = "manual" if (numero, us) in manual else "sin_escenarios"
            filas.append({
                "spec": numero, "carpeta": spec["carpeta"], "historia": us, "titulo": info["titulo"],
                "prioridad": info["prioridad"], "estado": estado, "escenarios": len(casos),
                "pasaron": conteo["passed"], "criterios": sorted({t for c in casos for t in c["tags"] if t.startswith("CA-")},
                                                                 key=lambda t: [int(x) for x in t[3:].split(".")]),
                "nota": manual.get((numero, us), ""),
            })
    return filas


# --- Consolidación --------------------------------------------------------------------------

def consolidar(suites: list[dict], args) -> dict:
    pruebas = [{**p, "componente": s["componente"]} for s in suites for p in s["pruebas"]]
    totales = Counter(p["resultado"] for p in pruebas)

    def agrupar(clave):
        grupos = defaultdict(Counter)
        for p in pruebas:
            grupos[p[clave]][p["resultado"]] += 1
        return {k: dict(v) for k, v in grupos.items()}

    no_ejecutadas = [s["componente"] for s in suites if not s["ejecutada"]]
    if no_ejecutadas:
        veredicto = "NO EJECUTADO"
    elif totales["failed"] or totales["error"]:
        veredicto = "FALLÓ"
    elif not pruebas:
        veredicto = "SIN PRUEBAS"
    else:
        veredicto = "PASÓ"
    return {
        "veredicto": veredicto,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "filtros": {"tipo": args.tipo, "componentes": [s["componente"] for s in suites], "rapido": args.rapido},
        "duracion": round(sum(s["duracion"] for s in suites), 2),
        "totales": {"total": len(pruebas), "pasaron": totales["passed"], "fallaron": totales["failed"],
                    "errores": totales["error"], "omitidas": totales["skipped"]},
        "suites": [{"componente": s["componente"], "ejecutada": s["ejecutada"], "duracion": s["duracion"],
                    **{k: Counter(p["resultado"] for p in s["pruebas"])[k] for k in ESTADOS}} for s in suites],
        "suites_no_ejecutadas": no_ejecutadas,
        "por_tipo": agrupar("tipo"),
        "por_nivel": agrupar("nivel"),
        # Una historia puede estar cubierta por otro componente: la matriz solo es fiable con todos.
        "trazabilidad": trazabilidad(pruebas) if args.tipo != "tecnica" and not args.componente else [],
        "fallas": [p for p in pruebas if p["resultado"] in ("failed", "error")],
        "pruebas": pruebas,
    }


# --- Reportes -------------------------------------------------------------------------------

TRAZA_LABEL = {"passed": "Cubierta · pasó", "failed": "Cubierta · falló", "skipped": "Omitida",
               "manual": "Validación manual", "sin_escenarios": "Sin escenarios"}


def reporte_md(r: dict) -> str:
    icono = {"PASÓ": "✅", "FALLÓ": "❌"}.get(r["veredicto"], "⚠️")
    t = r["totales"]
    lines = [
        f"# Reporte de pruebas — {icono} {r['veredicto']}",
        "",
        f"{r['fecha']} · {t['total']} pruebas en {r['duracion']} s · tipo: {r['filtros']['tipo']}"
        + (" · sin contrato" if r["filtros"]["rapido"] else ""),
        "",
        f"**{t['pasaron']} pasaron · {t['fallaron']} fallaron · {t['errores']} con error · {t['omitidas']} omitidas**",
        "",
        "| Componente | Pasaron | Fallaron | Errores | Omitidas | Duración |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for s in r["suites"]:
        nombre = s["componente"] + ("" if s["ejecutada"] else " ⚠️ no se ejecutó")
        lines.append(f"| {nombre} | {s['passed']} | {s['failed']} | {s['error']} | {s['skipped']} | {s['duracion']} s |")
    lines += ["", "| Tipo | Nivel | Pasaron | Total |", "|---|---|---:|---:|"]
    niveles = defaultdict(Counter)
    for p in r["pruebas"]:
        niveles[(p["tipo"], p["nivel"])][p["resultado"]] += 1
    for (tipo, nivel), c in sorted(niveles.items(), key=lambda kv: (kv[0][0], NIVELES.index(kv[0][1]))):
        lines.append(f"| {tipo} | {nivel} | {c['passed']} | {sum(c.values())} |")
    if r["trazabilidad"]:
        lines += ["", "## Trazabilidad de historias de usuario", "",
                  "| Spec | Historia | Estado | Escenarios | Criterios |", "|---|---|---|---:|---|"]
        for f in r["trazabilidad"]:
            lines.append(f"| {f['spec']} | {f['historia']} {f['titulo']} | {TRAZA_LABEL[f['estado']]} | "
                         f"{f['pasaron']}/{f['escenarios']} | {', '.join(f['criterios']) or f['nota']} |")
    if r["fallas"]:
        lines += ["", "## Fallas", ""]
        for f in r["fallas"]:
            detalle = f["detalle"].strip().splitlines()
            lines += [f"- **{f['componente']}** · {f['titulo']}  ", f"  `{f['id']}`", "  ```",
                      *[f"  {line}" for line in detalle[-15:]], "  ```"]
    return "\n".join(lines) + "\n"


CSS = """
:root{--ink:#141413;--ink7:#3A3935;--mist50:#FAF9F7;--mist100:#F4F3EF;--mist200:#E9E7E1;--mist500:#75726A;
--accent:#E3622E;--ok:#047857;--okbg:#ECFDF5;--bad:#B91C1C;--badbg:#FEF2F2;--warn:#B45309;--warnbg:#FFFBEB}
*{box-sizing:border-box}body{margin:0;background:var(--mist50);color:var(--ink);font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:32px 16px 64px}h1{font-size:20px;margin:0}h2{font-size:15px;margin:32px 0 12px}
.muted{color:var(--mist500);font-size:12.5px}.banner{display:flex;align-items:center;gap:16px;padding:20px;border-radius:14px;border:1px solid var(--mist200);background:#fff;margin:20px 0}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:600}
.v-ok{background:var(--okbg);color:var(--ok)}.v-bad{background:var(--badbg);color:var(--bad)}.v-warn{background:var(--warnbg);color:var(--warn)}.v-neutral{background:var(--mist100);color:var(--ink7)}
.verdict{font-size:22px;font-weight:700;padding:10px 18px;border-radius:12px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}.kpi{background:#fff;border:1px solid var(--mist200);border-radius:12px;padding:14px}
.kpi b{display:block;font-size:24px}table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--mist200);border-radius:12px;overflow:hidden}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--mist100);vertical-align:top}th{background:var(--mist50);font-size:12px;color:var(--mist500);font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums}.table-wrap{overflow-x:auto}details{background:#fff;border:1px solid var(--mist200);border-radius:10px;margin:8px 0}
summary{cursor:pointer;padding:10px 14px}pre{margin:0;padding:12px 14px;background:var(--ink);color:#eee;font-size:12px;overflow-x:auto;border-radius:0 0 10px 10px}
input{width:100%;padding:8px 12px;border:1px solid var(--mist200);border-radius:8px;font:inherit;margin-bottom:10px}code{font-size:12px}
.bar{height:6px;border-radius:999px;background:var(--mist100);overflow:hidden;margin-top:8px}.bar span{display:block;height:100%;background:var(--ok)}
"""


def reporte_html(r: dict) -> str:
    e = html.escape
    t = r["totales"]
    tono = {"PASÓ": "v-ok", "FALLÓ": "v-bad"}.get(r["veredicto"], "v-warn")
    estado_tono = {"passed": "v-ok", "failed": "v-bad", "error": "v-bad", "skipped": "v-neutral",
                   "manual": "v-warn", "sin_escenarios": "v-warn"}
    pct = (t["pasaron"] / t["total"] * 100) if t["total"] else 0

    def kpi(label, value, extra=""):
        return f'<div class="kpi"><span class="muted">{label}</span><b>{value}</b>{extra}</div>'

    suites = "".join(
        f"<tr><td>{e(s['componente'])}{'' if s['ejecutada'] else ' <span class=\"badge v-bad\">no se ejecutó</span>'}</td>"
        f"<td class=n>{s['passed']}</td><td class=n>{s['failed']}</td><td class=n>{s['error']}</td>"
        f"<td class=n>{s['skipped']}</td><td class=n>{s['duracion']} s</td></tr>" for s in r["suites"])
    niveles = defaultdict(Counter)
    for p in r["pruebas"]:
        niveles[(p["tipo"], p["nivel"])][p["resultado"]] += 1
    filas_nivel = "".join(
        f"<tr><td>{'Funcional' if tipo == 'funcional' else 'Técnica'}</td><td>{e(nivel)}</td>"
        f"<td class=n>{c['passed']}</td><td class=n>{c['failed'] + c['error']}</td><td class=n>{sum(c.values())}</td></tr>"
        for (tipo, nivel), c in sorted(niveles.items(), key=lambda kv: (kv[0][0], NIVELES.index(kv[0][1]))))
    traza = "".join(
        f"<tr><td>{f['spec']}</td><td><b>{f['historia']}</b> {e(f['titulo'])} <span class=muted>{f['prioridad']}</span></td>"
        f"<td><span class='badge {estado_tono[f['estado']]}'>{TRAZA_LABEL[f['estado']]}</span></td>"
        f"<td class=n>{f['pasaron']}/{f['escenarios']}</td><td class=muted>{e(', '.join(f['criterios']) or f['nota'].replace('`', ''))}</td></tr>"
        for f in r["trazabilidad"])
    fallas = "".join(
        f"<details open><summary><span class='badge v-bad'>{ESTADOS[f['resultado']]}</span> "
        f"<b>{e(f['componente'])}</b> · {e(f['titulo'])}<br><code class=muted>{e(f['id'])}</code></summary>"
        f"<pre>{e(f['detalle'][-3000:])}</pre></details>" for f in r["fallas"])
    todas = "".join(
        f"<tr data-q=\"{e((p['componente'] + ' ' + p['titulo'] + ' ' + p['id'] + ' ' + ' '.join(p['tags'])).lower())}\">"
        f"<td><span class='badge {estado_tono[p['resultado']]}'>{ESTADOS[p['resultado']]}</span></td>"
        f"<td>{e(p['componente'])}</td><td>{'Funcional' if p['tipo'] == 'funcional' else 'Técnica'} · {e(p['nivel'])}</td>"
        f"<td>{e(p['titulo'])}<br><span class=muted>{e(' '.join(p['tags']))}</span></td><td class=n>{p['duracion']:.2f} s</td></tr>"
        for p in sorted(r["pruebas"], key=lambda p: (p["resultado"] == "passed", p["componente"], p["id"])))

    traza_html = (f"<h2>Trazabilidad de historias de usuario</h2><div class=table-wrap><table><tr><th>Spec</th><th>Historia</th>"
                  f"<th>Estado</th><th>Escenarios</th><th>Criterios / nota</th></tr>{traza}</table></div>") if traza else ""
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reporte de pruebas · TokenIO</title><style>{CSS}</style></head><body><main>
<h1>Reporte de pruebas · TokenIO</h1>
<p class=muted>{e(r['fecha'])} · tipo: {e(r['filtros']['tipo'])} · componentes: {e(', '.join(r['filtros']['componentes']))}{' · sin contrato' if r['filtros']['rapido'] else ''}</p>
<div class=banner><span class="verdict {tono}">{e(r['veredicto'])}</span>
<div><b>{t['pasaron']} de {t['total']} pruebas pasaron</b> en {r['duracion']} s<div class=bar><span style="width:{pct:.1f}%"></span></div></div></div>
<div class=kpis>{kpi('Pasaron', t['pasaron'])}{kpi('Fallaron', t['fallaron'])}{kpi('Con error', t['errores'])}{kpi('Omitidas', t['omitidas'])}</div>
<h2>Por componente</h2><div class=table-wrap><table><tr><th>Componente</th><th>Pasaron</th><th>Fallaron</th><th>Errores</th><th>Omitidas</th><th>Duración</th></tr>{suites}</table></div>
<h2>Por tipo y nivel</h2><div class=table-wrap><table><tr><th>Tipo</th><th>Nivel</th><th>Pasaron</th><th>Fallaron</th><th>Total</th></tr>{filas_nivel}</table></div>
{traza_html}
{'<h2>Fallas</h2>' + fallas if fallas else ''}
<h2>Todas las pruebas</h2><input id=q placeholder="Filtrar por componente, nombre o tag (ej. US-4, contrato, governance)…">
<div class=table-wrap><table id=t><tr><th>Estado</th><th>Componente</th><th>Tipo</th><th>Prueba</th><th>Duración</th></tr>{todas}</table></div>
</main><script>
document.getElementById('q').addEventListener('input',function(){{var q=this.value.toLowerCase();
document.querySelectorAll('#t tr[data-q]').forEach(function(r){{r.style.display=r.dataset.q.indexOf(q)>=0?'':'none';}});}});
</script></body></html>
"""


def main() -> int:
    args = parse_args()
    salida = (REPO / args.salida).resolve()
    salida.mkdir(parents=True, exist_ok=True)
    componentes = args.componente or list(COMPONENTES)

    print(f"Pruebas de TokenIO · tipo: {args.tipo}{' · sin contrato' if args.rapido else ''}")
    suites = []
    for nombre in componentes:
        print(f"  {nombre:<11} ", end="", flush=True)
        suite = run_suite(nombre, COMPONENTES[nombre], args, salida)
        c = Counter(p["resultado"] for p in suite["pruebas"])
        estado = "no se ejecutó (ver log)" if not suite["ejecutada"] else \
            f"{c['passed']} pasaron, {c['failed']} fallaron, {c['error']} errores, {c['skipped']} omitidas"
        print(f"{estado} · {suite['duracion']} s")
        suites.append(suite)

    resultado = consolidar(suites, args)
    (salida / "resumen.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    (salida / "reporte.md").write_text(reporte_md(resultado), encoding="utf-8")
    (salida / "reporte.html").write_text(reporte_html(resultado), encoding="utf-8")

    t = resultado["totales"]
    print(f"\nVeredicto: {resultado['veredicto']} · {t['pasaron']}/{t['total']} pasaron")
    for falla in resultado["fallas"]:
        print(f"  ✗ [{falla['componente']}] {falla['id']}")
    pendientes = [f for f in resultado["trazabilidad"] if f["estado"] == "sin_escenarios"]
    for f in pendientes:
        print(f"  ! spec {f['spec']} {f['historia']} no tiene escenarios ni validación manual declarada")
    print(f"Reporte: {salida / 'reporte.html'}")
    if resultado["suites_no_ejecutadas"]:
        return 2
    return 1 if resultado["veredicto"] == "FALLÓ" else 0


if __name__ == "__main__":
    sys.exit(main())
