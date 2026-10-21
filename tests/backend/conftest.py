"""Entorno aislado del backend: SQLite temporal, motor de modelos simulado y sesiones por rol.

Las variables se fijan antes de importar `app`: config.py las lee al importarse y
load_dotenv no sobrescribe las que ya existen, así el backend/.env del desarrollador
no afecta las pruebas.
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

REPO = Path(__file__).resolve().parents[2]
_TMP = Path(tempfile.mkdtemp(prefix="tokenio-backend-"))

os.environ.update({
    "DATABASE_URL": f"sqlite:///{(_TMP / 'playground.db').as_posix()}",
    "SECRET_KEY": "clave-solo-para-pruebas",
    "SEED_DEMO_ACTIVITY": "false",
    "DEFAULT_CHAT_MODEL": "modelo-prueba:latest",
    "EMBED_MODEL": "embed-prueba",
    "OLLAMA_HOST": "http://ollama.invalid:9",
    "LLM_GATEWAY_URL": "",
    "GOVERNANCE_URL": "http://governance.invalid:9",
    "SERVICE_TOKEN": "token-servicio-pruebas",
    "GATEWAY_FERNET_KEY": Fernet.generate_key().decode(),
})
sys.path.insert(0, str(REPO / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, SQLModel  # noqa: E402

from app import ollama_client, security  # noqa: E402
from app.database import engine, init_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.seed import DEMO_PASSWORD, run_seed, seed_sample_knowledge  # noqa: E402

from fakes import FakeLLM  # noqa: E402
from support import ORIGINALS, auth_headers  # noqa: E402

# Hash de contraseñas barato en pruebas: verify_password lee las rondas del hash guardado.
security._PBKDF2_ROUNDS = 1_000

_FAKE = FakeLLM()


@pytest.fixture(scope="session", autouse=True)
def _patch_model_engine():
    mp = pytest.MonkeyPatch()
    for name in ORIGINALS:
        mp.setattr(ollama_client, name, getattr(_FAKE, name))
    yield
    mp.undo()


@pytest.fixture
def fake_llm():
    return _FAKE


@pytest.fixture(autouse=True)
def fresh_db():
    """Cada prueba parte de los datos de demostración, sin restos de otras pruebas."""
    _FAKE.reset()
    SQLModel.metadata.drop_all(engine)
    init_db()
    run_seed()
    asyncio.run(seed_sample_knowledge())
    _FAKE.reset()
    yield


@pytest.fixture
def client():
    return TestClient(fastapi_app)


@pytest.fixture
def db():
    with Session(engine) as session:
        yield session


@pytest.fixture
def as_role():
    return auth_headers


@pytest.fixture
def demo_password():
    return DEMO_PASSWORD
