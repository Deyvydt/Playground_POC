"""Arranca Postgres local y el gateway LiteLLM con las variables de .env."""
import importlib.metadata
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

import certs
import start_db

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

LANGFUSE_SETTINGS = {
    "success_callback": ["langfuse"],
    "failure_callback": ["langfuse"],
    # Solo tokens, costo, latencia y errores: el texto de prompts y respuestas no sale del gateway.
    "turn_off_message_logging": True,
}


def langfuse_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def effective_config() -> Path:
    """config.yaml tal cual, o una copia con los callbacks de Langfuse si hay credenciales en .env.

    Así el gateway arranca igual sin Langfuse, y nadie edita config.yaml para activarlo.
    """
    base = HERE / "config.yaml"
    if not langfuse_enabled():
        return base
    import yaml

    config = yaml.safe_load(base.read_text(encoding="utf-8"))
    config.setdefault("litellm_settings", {}).update(LANGFUSE_SETTINGS)
    target = HERE.parent / ".data" / "gateway-config.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return target


def ensure_prisma_client() -> None:
    """La imagen Docker de LiteLLM trae el cliente Prisma generado; con pip hay que generarlo una vez por versión."""
    import litellm

    version = importlib.metadata.version("litellm")
    marker = HERE.parent / ".data" / f"prisma-generated-{version}"
    if marker.exists():
        return
    schema = Path(litellm.__file__).parent / "proxy" / "schema.prisma"
    subprocess.check_call([str(Path(sys.executable).parent / "prisma"), "generate", "--schema", str(schema)], cwd=HERE)
    marker.touch()


if __name__ == "__main__":
    certs.apply_to_env()
    os.environ["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}"
    # En Windows la codificación por defecto es cp1252 y Prisma escribe archivos con UTF-8.
    os.environ["PYTHONUTF8"] = "1"
    ensure_prisma_client()
    start_db.start()
    litellm = Path(sys.executable).parent / "litellm"
    config = effective_config()
    print(f"Trazas en Langfuse: {'activadas (' + os.getenv('LANGFUSE_HOST', 'cloud') + ')' if langfuse_enabled() else 'desactivadas'}")
    cmd = [
        str(litellm),
        "--config", str(config),
        "--host", os.getenv("GATEWAY_HOST", "127.0.0.1"),
        "--port", os.getenv("GATEWAY_PORT", "4000"),
    ]
    sys.exit(subprocess.call(cmd, cwd=HERE))
