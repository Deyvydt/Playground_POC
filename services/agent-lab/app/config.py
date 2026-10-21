import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres@127.0.0.1:5433/agentlab")

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:4000")

GOVERNANCE_URL = os.getenv("GOVERNANCE_URL", "http://127.0.0.1:8100")
IDENTITY_URL = os.getenv("IDENTITY_URL", "http://127.0.0.1:8000")
SERVICE_TOKEN = os.environ["SERVICE_TOKEN"]

LAB_FERNET_KEY = os.environ["LAB_FERNET_KEY"]

CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")
