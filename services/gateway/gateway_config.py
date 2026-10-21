"""Config efectiva del gateway: config.yaml tal cual, o una copia con los callbacks de Langfuse.

Lo usan start.py (instalación con pip) y docker-compose.yml (imagen oficial de LiteLLM),
para que nadie edite config.yaml al activar Langfuse.

Uso: python gateway_config.py <destino.yaml>   -> imprime la ruta de la config a usar
"""
import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent

LANGFUSE_SETTINGS = {
    "success_callback": ["langfuse"],
    "failure_callback": ["langfuse"],
    # Solo tokens, costo, latencia y errores: el texto de prompts y respuestas no sale del gateway.
    "turn_off_message_logging": True,
}


def langfuse_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def effective_config(target: Path, base: Path = HERE / "config.yaml") -> Path:
    if not langfuse_enabled():
        return base
    config = yaml.safe_load(base.read_text(encoding="utf-8"))
    config.setdefault("litellm_settings", {}).update(LANGFUSE_SETTINGS)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return target


if __name__ == "__main__":
    print(effective_config(Path(sys.argv[1])))
