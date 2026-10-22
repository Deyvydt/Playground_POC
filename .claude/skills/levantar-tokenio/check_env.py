"""Valida los .env de TokenIO sin imprimir secretos.

Revisa formato, placeholders, prefijos de keys, claves Fernet y que los valores
compartidos coincidan entre servicios. Uso, desde la raíz del repo:

    services\\gateway\\.venv\\Scripts\\python .claude\\skills\\levantar-tokenio\\check_env.py

Código de salida 0 = todo bien.
"""
import re
import sys
from pathlib import Path

from cryptography.fernet import Fernet

FILES = {
    "gateway": Path("services/gateway/.env"),
    "governance": Path("services/governance/.env"),
    "agent-lab": Path("services/agent-lab/.env"),
    "backend": Path("backend/.env"),
}
REQUIRED = {
    "gateway": ["LITELLM_MASTER_KEY", "LITELLM_SALT_KEY", "DATABASE_URL", "OLLAMA_API_BASE", "WEBHOOK_URL"],
    "governance": ["LITELLM_MASTER_KEY", "SERVICE_TOKEN", "WEBHOOK_TOKEN"],
    "agent-lab": ["SERVICE_TOKEN", "LAB_FERNET_KEY"],
    "backend": ["SECRET_KEY", "LLM_GATEWAY_URL", "GOVERNANCE_URL", "SERVICE_TOKEN", "GATEWAY_FERNET_KEY"],
}
PREFIX = {"LITELLM_MASTER_KEY": "sk-", "LITELLM_SALT_KEY": "sk-",
          "LANGFUSE_PUBLIC_KEY": "pk-lf-", "LANGFUSE_SECRET_KEY": "sk-lf-"}
FERNET = {"LAB_FERNET_KEY", "GATEWAY_FERNET_KEY"}
errors: list[str] = []


def load(name: str, path: Path) -> dict[str, str]:
    if not path.exists():
        errors.append(f"{name}: falta {path} (copiar desde .env.example)")
        return {}
    values = {}
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
        if not m:
            errors.append(f"{name}:{n}: formato inválido (¿espacios alrededor del '='?)")
            continue
        key, value = m.groups()
        if value != value.strip() or value[:1] in "\"'":
            errors.append(f"{name}: {key} tiene espacios o comillas")
        if "cambia-est" in value or "copiar-de" in value:
            errors.append(f"{name}: {key} sigue con el valor de ejemplo")
        if key in PREFIX and not value.startswith(PREFIX[key]):
            errors.append(f"{name}: {key} debe empezar con {PREFIX[key]}")
        if key in FERNET:
            try:
                Fernet(value.encode())
            except Exception:  # noqa: BLE001
                errors.append(f"{name}: {key} no es una clave Fernet válida")
        values[key] = value
    for key in REQUIRED[name]:
        if not values.get(key):
            errors.append(f"{name}: falta {key} (o está comentada)")
    return values


env = {name: load(name, path) for name, path in FILES.items()}
hook = re.search(r"\?token=(.+)$", env["gateway"].get("WEBHOOK_URL", ""))
pairs = [
    ("LITELLM_MASTER_KEY gateway = governance", env["gateway"].get("LITELLM_MASTER_KEY"), env["governance"].get("LITELLM_MASTER_KEY")),
    ("token de WEBHOOK_URL (gateway) = WEBHOOK_TOKEN (governance)", hook and hook[1], env["governance"].get("WEBHOOK_TOKEN")),
    ("SERVICE_TOKEN governance = agent-lab", env["governance"].get("SERVICE_TOKEN"), env["agent-lab"].get("SERVICE_TOKEN")),
    ("SERVICE_TOKEN governance = backend", env["governance"].get("SERVICE_TOKEN"), env["backend"].get("SERVICE_TOKEN")),
]
for label, a, b in pairs:
    if not a or a != b:
        errors.append(f"no coinciden: {label}")

langfuse = env["gateway"].get("LANGFUSE_PUBLIC_KEY") and env["gateway"].get("LANGFUSE_SECRET_KEY")
print(f"Langfuse: {'activado' if langfuse else 'desactivado (opcional)'}")
if errors:
    print("\n".join(f"X {e}" for e in errors))
    sys.exit(1)
print("OK: los 4 .env están completos y los valores compartidos coinciden")
