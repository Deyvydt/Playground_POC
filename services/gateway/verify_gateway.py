"""Verifica las reglas de gobierno del gateway con keys temporales.

Casos: llamada válida, modelo no permitido, presupuesto excedido y key bloqueada.
Uso: python verify_gateway.py   (requiere el gateway corriendo y bootstrap.py ejecutado)
"""
import sys
import time

from admin import client

PROMPT = [{"role": "user", "content": "Responde solo con la palabra: ok"}]


def new_key(admin, alias: str, **fields) -> str:
    body = {"key_alias": alias, "team_id": "plataforma", "metadata": {"origen": "verify_gateway"}, **fields}
    r = admin.post("/key/generate", json=body)
    r.raise_for_status()
    return r.json()["key"]


def chat(key: str, model: str = "llama-local"):
    with client(key) as c:
        return c.post("/v1/chat/completions", json={"model": model, "messages": PROMPT, "max_tokens": 5})


def error_text(response) -> str:
    try:
        return str(response.json().get("error", {}).get("message", ""))[:140]
    except ValueError:
        return response.text[:140]


def case_valid(admin, keys):
    key = new_key(admin, "verify-valida", models=["local-models"])
    keys.append(key)
    r = chat(key)
    return r.status_code == 200, f"HTTP {r.status_code}"


def case_model_not_allowed(admin, keys):
    key = new_key(admin, "verify-modelo", models=["embed-local"])
    keys.append(key)
    r = chat(key, "llama-local")
    return r.status_code in (401, 403), f"HTTP {r.status_code}: {error_text(r)}"


def case_budget_exceeded(admin, keys):
    key = new_key(admin, "verify-presupuesto", models=["local-models"], max_budget=0.0000001)
    keys.append(key)
    first = chat(key)
    if first.status_code != 200:
        return False, f"la primera llamada debía pasar y dio HTTP {first.status_code}"
    # El gasto se acumula tras la respuesta; se reintenta unos segundos hasta ver el rechazo.
    for _ in range(10):
        time.sleep(2)
        r = chat(key)
        if r.status_code != 200:
            return "budget" in error_text(r).lower(), f"HTTP {r.status_code}: {error_text(r)}"
    return False, "el gateway siguió aceptando llamadas"


def case_blocked(admin, keys):
    key = new_key(admin, "verify-bloqueada", models=["local-models"])
    keys.append(key)
    admin.post("/key/block", json={"key": key}).raise_for_status()
    r = chat(key)
    return r.status_code in (401, 403), f"HTTP {r.status_code}: {error_text(r)}"


CASES = [
    ("Key válida responde", case_valid),
    ("Modelo no permitido es rechazado", case_model_not_allowed),
    ("Presupuesto excedido es rechazado", case_budget_exceeded),
    ("Key bloqueada es rechazada", case_blocked),
]


def main() -> int:
    keys: list[str] = []
    failures = 0
    with client() as admin:
        try:
            for name, case in CASES:
                ok, detail = case(admin, keys)
                failures += not ok
                print(f"[{'OK' if ok else 'FALLA'}] {name} — {detail}")
        finally:
            if keys:
                admin.post("/key/delete", json={"keys": keys})
    print(f"\n{len(CASES) - failures}/{len(CASES)} casos correctos")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
