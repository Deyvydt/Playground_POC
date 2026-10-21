import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres@127.0.0.1:5433/governance")

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:4000")
GATEWAY_PUBLIC_URL = os.getenv("GATEWAY_PUBLIC_URL", GATEWAY_URL)
LITELLM_MASTER_KEY = os.environ["LITELLM_MASTER_KEY"]

IDENTITY_URL = os.getenv("IDENTITY_URL", "http://127.0.0.1:8000")
SERVICE_TOKEN = os.environ["SERVICE_TOKEN"]
WEBHOOK_TOKEN = os.environ["WEBHOOK_TOKEN"]

MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL_SECONDS", "60"))
BUDGET_WARNING_RATIO = float(os.getenv("BUDGET_WARNING_RATIO", "0.8"))
ERROR_RATE_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", "0.5"))
ERROR_WINDOW_MINUTES = int(os.getenv("ERROR_WINDOW_MINUTES", "10"))
ERROR_MIN_CALLS = int(os.getenv("ERROR_MIN_CALLS", "5"))

CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")

DEFAULT_MODELS = ["local-models"]
