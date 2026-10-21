"""Arranca Postgres local y el gateway LiteLLM con las variables de .env."""
import importlib.metadata
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

import certs
import gateway_config
import start_db

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

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
    config = gateway_config.effective_config(HERE.parent / ".data" / "gateway-config.yaml")
    langfuse = f"activadas ({os.getenv('LANGFUSE_HOST', 'cloud')})" if gateway_config.langfuse_enabled() else "desactivadas"
    print(f"Trazas en Langfuse: {langfuse}")
    cmd = [
        str(litellm),
        "--config", str(config),
        "--host", os.getenv("GATEWAY_HOST", "127.0.0.1"),
        "--port", os.getenv("GATEWAY_PORT", "4000"),
    ]
    sys.exit(subprocess.call(cmd, cwd=HERE))
