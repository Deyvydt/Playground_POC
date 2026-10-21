import pytest


def test_login_correcto_devuelve_token_y_perfil_sin_contrasena(client, demo_password):
    r = client.post("/api/auth/login", json={"email": "ana.rios@tcs.com", "password": demo_password})
    assert r.status_code == 200
    body = r.json()
    assert body["token"] and body["user"]["role"] == "admin"
    assert "password_hash" not in body["user"]
    assert "govern" in body["user"]["permissions"]


def test_login_ignora_mayusculas_y_espacios_del_correo(client, demo_password):
    r = client.post("/api/auth/login", json={"email": "  Ana.Rios@TCS.com ", "password": demo_password})
    assert r.status_code == 200


@pytest.mark.parametrize("email, password", [
    ("ana.rios@tcs.com", "incorrecta"),
    ("nadie@tcs.com", "Tcs2026!"),
])
def test_login_con_credenciales_invalidas_responde_401_sin_revelar_cual_fallo(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 401
    assert r.json()["detail"] == "Correo o contraseña incorrectos"


def test_me_devuelve_el_usuario_de_la_sesion(client, as_role):
    r = client.get("/api/auth/me", headers=as_role("developer"))
    assert r.status_code == 200 and r.json()["email"] == "carlos.vega@tcs.com"


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer token-falso"}, {"Authorization": "Basic abc"}])
def test_rutas_protegidas_sin_sesion_valida_responden_401(client, headers):
    assert client.get("/api/agents", headers=headers).status_code == 401


def test_sesion_de_un_usuario_desactivado_deja_de_valer(client, as_role):
    headers = as_role("developer")
    admin = as_role("admin")
    user_id = client.get("/api/auth/me", headers=headers).json()["id"]
    client.put(f"/api/users/{user_id}", json={"is_active": False}, headers=admin)
    assert client.get("/api/auth/me", headers=headers).status_code == 401
