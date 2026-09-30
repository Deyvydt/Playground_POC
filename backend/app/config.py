import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'data' / 'playground.db').as_posix()}")
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K_CHUNKS = 4
