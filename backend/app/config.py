import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'data' / 'playground.db').as_posix()}")
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")

# Firma de los tokens de sesion. En cualquier entorno compartido debe venir del entorno.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "12"))

# Siembra historial de uso para que el panel no arranque vacio en una instalacion nueva.
SEED_DEMO_ACTIVITY = os.getenv("SEED_DEMO_ACTIVITY", "true").lower() == "true"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K_CHUNKS = 4
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
