"""Valores límite y particiones de equivalencia del backend.

Para cada regla con rango se prueban los cuatro puntos clásicos: justo debajo del
mínimo, el mínimo, el máximo y justo encima del máximo.
"""
import pytest

from app.routers import knowledge

AGENTE = {"name": "Agente Límite", "role_prompt": "Instrucciones válidas."}
USUARIO = {"name": "Usuario Límite", "email": "limite@tcs.com", "password": "Clave1"}


@pytest.mark.limites
@pytest.mark.parametrize("temperatura, status", [(-0.01, 422), (0, 201), (1, 201), (1.01, 422)])
def test_temperatura_del_agente_entre_0_y_1(client, as_role, temperatura, status):
    r = client.post("/api/agents", json={**AGENTE, "temperature": temperatura}, headers=as_role("developer"))
    assert r.status_code == status


@pytest.mark.limites
@pytest.mark.parametrize("campo, valor, status", [
    ("name", "A", 422), ("name", "AB", 201),
    ("role_prompt", "1234", 422), ("role_prompt", "12345", 201),
])
def test_longitud_minima_de_nombre_e_instrucciones(client, as_role, campo, valor, status):
    r = client.post("/api/agents", json={**AGENTE, campo: valor}, headers=as_role("developer"))
    assert r.status_code == status


@pytest.mark.limites
@pytest.mark.parametrize("campo, valor, status", [
    ("password", "12345", 422), ("password", "123456", 201),
    ("name", "U", 422), ("name", "Ul", 201),
    ("email", "a@", 422), ("email", "a@b", 201),
])
def test_longitudes_minimas_al_crear_usuarios(client, as_role, campo, valor, status):
    r = client.post("/api/users", json={**USUARIO, campo: valor}, headers=as_role("admin"))
    assert r.status_code == status


@pytest.mark.limites
@pytest.mark.parametrize("ruta", ["/api/metrics/summary", "/api/metrics/timeseries"])
@pytest.mark.parametrize("dias, status", [(0, 422), (1, 200), (365, 200), (366, 422)])
def test_periodo_de_consumo_entre_1_y_365_dias(client, as_role, ruta, dias, status):
    assert client.get(f"{ruta}?days={dias}", headers=as_role("developer")).status_code == status


@pytest.mark.limites
@pytest.mark.parametrize("limite, status", [(0, 422), (1, 200), (50, 200), (51, 422)])
def test_actividad_reciente_entre_1_y_50_registros(client, as_role, limite, status):
    assert client.get(f"/api/metrics/activity?limit={limite}", headers=as_role("developer")).status_code == status


@pytest.mark.limites
def test_actividad_reciente_devuelve_como_maximo_el_limite_pedido(client, as_role):
    dev = as_role("developer")
    for i in range(3):
        client.post("/api/agents/1/chat", json={"message": f"m{i}"}, headers=dev)
    assert len(client.get("/api/metrics/activity?limit=1", headers=dev).json()) == 1
    assert len(client.get("/api/metrics/activity?limit=50", headers=dev).json()) == 3


@pytest.mark.limites
@pytest.mark.parametrize("tamano, status", [(10, 201), (11, 413)])
def test_tamano_maximo_de_documento(client, as_role, monkeypatch, tamano, status):
    monkeypatch.setattr(knowledge, "MAX_UPLOAD_BYTES", 10)
    r = client.post("/api/agents/5/knowledge", files={"file": ("a.txt", b"x" * tamano)}, headers=as_role("developer"))
    assert r.status_code == status


@pytest.mark.limites
@pytest.mark.parametrize("mensaje, status", [("", 422), ("?", 200)])
def test_mensaje_de_chat_de_al_menos_un_caracter(client, as_role, mensaje, status):
    assert client.post("/api/agents/1/chat", json={"message": mensaje}, headers=as_role("viewer")).status_code == status


@pytest.mark.limites
@pytest.mark.parametrize("pipeline, status", [([], 422), ([2], 200), ([2, 3, 2], 200)])
def test_un_flujo_necesita_al_menos_un_agente(client, as_role, pipeline, status):
    r = client.post("/api/orchestration/run", json={"input_text": "x", "pipeline": pipeline}, headers=as_role("viewer"))
    assert r.status_code == status


@pytest.mark.particion
@pytest.mark.parametrize("archivo, status", [
    ("doc.txt", 201), ("doc.md", 201), ("DOC.TXT", 201),   # válidos (sin importar mayúsculas)
    ("doc.csv", 400), ("doc.docx", 400), ("doc", 400),     # inválidos
])
def test_particion_de_formatos_de_documento(client, as_role, archivo, status):
    r = client.post("/api/agents/5/knowledge", files={"file": (archivo, b"contenido de prueba")}, headers=as_role("developer"))
    assert r.status_code == status


@pytest.mark.particion
@pytest.mark.parametrize("estado, status", [("active", 200), ("inactive", 409)])
def test_particion_por_estado_del_agente_al_conversar(client, as_role, estado, status):
    client.put("/api/agents/2", json={"status": estado}, headers=as_role("admin"))
    assert client.post("/api/agents/2/chat", json={"message": "Hola"}, headers=as_role("viewer")).status_code == status
