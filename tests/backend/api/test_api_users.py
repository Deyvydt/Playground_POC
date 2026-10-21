import pytest

NUEVO = {"name": "Pedro Prueba", "email": "Pedro.Prueba@tcs.com", "role": "developer", "password": "Temporal1"}


def test_admin_crea_usuario_con_correo_normalizado(client, as_role):
    r = client.post("/api/users", json=NUEVO, headers=as_role("admin"))
    assert r.status_code == 201
    assert r.json()["email"] == "pedro.prueba@tcs.com"
    assert "password_hash" not in r.json()


@pytest.mark.particion
def test_correo_duplicado_responde_409(client, as_role):
    r = client.post("/api/users", json={**NUEVO, "email": "ana.rios@tcs.com"}, headers=as_role("admin"))
    assert r.status_code == 409


@pytest.mark.particion
@pytest.mark.limites
@pytest.mark.parametrize("cambio", [{"password": "123"}, {"role": "superadmin"}, {"name": "P"}])
def test_datos_de_usuario_invalidos_responden_422(client, as_role, cambio):
    assert client.post("/api/users", json={**NUEVO, **cambio}, headers=as_role("admin")).status_code == 422


@pytest.mark.tabla_decision
def test_el_admin_no_puede_quitarse_su_rol_ni_desactivarse_ni_eliminarse(client, as_role):
    admin = as_role("admin")
    me = client.get("/api/auth/me", headers=admin).json()["id"]
    assert client.put(f"/api/users/{me}", json={"role": "viewer"}, headers=admin).status_code == 400
    assert client.put(f"/api/users/{me}", json={"is_active": False}, headers=admin).status_code == 400
    assert client.delete(f"/api/users/{me}", headers=admin).status_code == 400


def test_cambiar_contrasena_permite_entrar_con_la_nueva(client, as_role):
    admin = as_role("admin")
    user_id = client.post("/api/users", json=NUEVO, headers=admin).json()["id"]
    client.put(f"/api/users/{user_id}", json={"password": "NuevaClave9"}, headers=admin)
    assert client.post("/api/auth/login", json={"email": "pedro.prueba@tcs.com", "password": "NuevaClave9"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": "pedro.prueba@tcs.com", "password": "Temporal1"}).status_code == 401


def test_no_se_puede_cambiar_un_correo_a_uno_existente(client, as_role):
    admin = as_role("admin")
    user_id = client.post("/api/users", json=NUEVO, headers=admin).json()["id"]
    assert client.put(f"/api/users/{user_id}", json={"email": "LUCIA.SOTO@tcs.com"}, headers=admin).status_code == 409


def test_eliminar_usuario(client, as_role):
    admin = as_role("admin")
    user_id = client.post("/api/users", json=NUEVO, headers=admin).json()["id"]
    assert client.delete(f"/api/users/{user_id}", headers=admin).json() == {"ok": True}
    assert client.delete(f"/api/users/{user_id}", headers=admin).status_code == 404


def test_cualquier_usuario_puede_listar_usuarios_sin_ver_contrasenas(client, as_role):
    r = client.get("/api/users", headers=as_role("viewer"))
    assert r.status_code == 200 and len(r.json()) == 3
    assert all("password_hash" not in u for u in r.json())
