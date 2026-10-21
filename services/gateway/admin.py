"""Cliente mínimo de la API de administración del gateway, compartido por los scripts."""
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

GATEWAY_URL = os.getenv("GATEWAY_URL", f"http://127.0.0.1:{os.getenv('GATEWAY_PORT', '4000')}")
MASTER_KEY = os.environ["LITELLM_MASTER_KEY"]


def client(key: str = MASTER_KEY) -> httpx.Client:
    return httpx.Client(base_url=GATEWAY_URL, headers={"Authorization": f"Bearer {key}"}, timeout=120)
