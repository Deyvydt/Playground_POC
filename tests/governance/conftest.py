"""Entorno aislado de governance: SQLite temporal, gateway simulado y sesiones por rol.

La identidad real (backend /api/auth/me) se reemplaza con dependency_overrides: el rol viaja
en el token de prueba ("Bearer rol:admin"). La validación real del token tiene sus propias
pruebas unitarias (unit/test_auth.py).
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_TMP = Path(tempfile.mkdtemp(prefix="tokenio-governance-"))

os.environ.update({
    "DATABASE_URL": f"sqlite:///{(_TMP / 'governance.db').as_posix()}",
    "GATEWAY_URL": "http://gateway.invalid:9",
    "GATEWAY_PUBLIC_URL": "http://192.168.1.50:4000",
    "LITELLM_MASTER_KEY": "sk-master-pruebas",
    "IDENTITY_URL": "http://identity.invalid:9",
    "SERVICE_TOKEN": "token-servicio-pruebas",
    "WEBHOOK_TOKEN": "token-webhook-pruebas",
    "MONITOR_INTERVAL_SECONDS": "3600",
})
sys.path.insert(0, str(REPO / "services" / "governance"))

from fastapi import Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, SQLModel  # noqa: E402

from app import litellm_admin  # noqa: E402
from app.auth import Caller, get_caller  # noqa: E402
from app.database import engine, init_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.seed import run_seed  # noqa: E402

from fakes import FakeGateway  # noqa: E402

_GATEWAY = FakeGateway()
ADMIN_API = ("is_available", "generate_key", "update_key", "delete_key", "block_key", "unblock_key",
             "key_info", "team_info", "recent_logs")


async def caller_de_prueba(request: Request) -> Caller:
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token.startswith("rol:"):
        from fastapi import HTTPException
        raise HTTPException(401, "Sesión no válida o expirada")
    role = token.removeprefix("rol:")
    return Caller(name=f"Usuario {role}", role=role)


@pytest.fixture(scope="session", autouse=True)
def _patch_gateway():
    mp = pytest.MonkeyPatch()
    for name in ADMIN_API:
        mp.setattr(litellm_admin, name, getattr(_GATEWAY, name))
    fastapi_app.dependency_overrides[get_caller] = caller_de_prueba
    yield
    fastapi_app.dependency_overrides.clear()
    mp.undo()


@pytest.fixture
def gateway():
    return _GATEWAY


@pytest.fixture(autouse=True)
def fresh_db():
    _GATEWAY.reset()
    SQLModel.metadata.drop_all(engine)
    init_db()
    with Session(engine) as session:
        run_seed(session)
    yield


@pytest.fixture
def client():
    return TestClient(fastapi_app)


@pytest.fixture
def db():
    with Session(engine) as session:
        yield session


def as_role(role: str) -> dict:
    return {"Authorization": f"Bearer rol:{role}"}


@pytest.fixture
def headers():
    return as_role
