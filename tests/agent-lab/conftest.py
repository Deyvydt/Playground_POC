"""Entorno aislado de agent-lab: SQLite temporal, credenciales de los 8 nodos y modelo simulado."""
import os
import sys
import tempfile
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

REPO = Path(__file__).resolve().parents[2]
_TMP = Path(tempfile.mkdtemp(prefix="tokenio-agentlab-"))

os.environ.update({
    "DATABASE_URL": f"sqlite:///{(_TMP / 'agentlab.db').as_posix()}",
    "GATEWAY_URL": "http://gateway.invalid:9",
    "GOVERNANCE_URL": "http://governance.invalid:9",
    "IDENTITY_URL": "http://identity.invalid:9",
    "SERVICE_TOKEN": "token-servicio-pruebas",
    "LAB_FERNET_KEY": Fernet.generate_key().decode(),
})
sys.path.insert(0, str(REPO / "services" / "agent-lab"))

from fastapi import HTTPException, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from app import llm, secrets  # noqa: E402
from app.auth import Caller, get_caller  # noqa: E402
from app.database import engine, init_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

from fakes import FakeChatModel  # noqa: E402

NODOS = {
    "talentia": ["analizador_cv", "evaluador_ajuste", "generador_entrevista", "redactor_comunicaciones"],
    "agentfactory": ["generador_codigo", "revisor_codigo", "generador_tests", "documentador"],
}
_MODEL = FakeChatModel()


async def caller_de_prueba(request: Request) -> Caller:
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token.startswith("rol:"):
        raise HTTPException(401, "Sesión no válida o expirada")
    return Caller(name="Usuario de prueba", role=token.removeprefix("rol:"))


@pytest.fixture(scope="session", autouse=True)
def _patch_model():
    mp = pytest.MonkeyPatch()
    mp.setattr(llm, "ChatOpenAI", _MODEL.factory)
    fastapi_app.dependency_overrides[get_caller] = caller_de_prueba
    yield
    fastapi_app.dependency_overrides.clear()
    mp.undo()


@pytest.fixture(autouse=True)
def fresh_db():
    _MODEL.reset()
    SQLModel.metadata.drop_all(engine)
    init_db()
    agente_id = 0
    for sistema, nodos in NODOS.items():
        for nodo in nodos:
            agente_id += 1
            secrets.save(sistema, nodo, agente_id, f"{sistema}/{nodo}", f"sk-{nodo}")
    yield


@pytest.fixture
def model():
    return _MODEL


@pytest.fixture
def client():
    return TestClient(fastapi_app)


@pytest.fixture
def user():
    return {"Authorization": "Bearer rol:viewer"}
