import pytest
import time

from app import security


def test_hash_password_no_guarda_texto_plano_y_usa_sal_distinta():
    a = security.hash_password("Secreta1")
    b = security.hash_password("Secreta1")
    assert "Secreta1" not in a
    assert a != b
    assert a.startswith("pbkdf2$")


@pytest.mark.particion
def test_verify_password_acepta_la_correcta_y_rechaza_otras():
    stored = security.hash_password("Secreta1")
    assert security.verify_password("Secreta1", stored)
    assert not security.verify_password("secreta1", stored)


@pytest.mark.adivinanza_errores
def test_verify_password_con_hash_malformado_es_falso():
    assert not security.verify_password("x", "no-es-un-hash")


def test_token_firmado_identifica_al_usuario():
    assert security._decode_token(security.create_token(42)) == 42


@pytest.mark.adivinanza_errores
def test_token_alterado_es_rechazado():
    payload, signature = security.create_token(42).split(".")
    otro_payload = security.create_token(1).split(".")[0]
    assert security._decode_token(f"{otro_payload}.{signature}") is None
    assert security._decode_token(f"{payload}.firma-falsa") is None
    assert security._decode_token("sin-punto") is None


@pytest.mark.limites
def test_token_vencido_es_rechazado(monkeypatch):
    token = security.create_token(42)
    real_time = time.time
    monkeypatch.setattr(security.time, "time", lambda: real_time() + security.TOKEN_TTL_HOURS * 3600 + 1)
    assert security._decode_token(token) is None


@pytest.mark.tabla_decision
def test_permisos_por_rol_son_acumulativos():
    viewer, developer, admin = (security.PERMISSIONS[r] for r in ("viewer", "developer", "admin"))
    assert viewer < developer < admin
    assert "govern" in admin and "govern" not in developer
    assert "delete" not in developer


@pytest.mark.regresion
@pytest.mark.adivinanza_errores
def test_firma_con_caracteres_no_ascii_es_rechazada_sin_error():
    """Regresión: hmac.compare_digest lanzaba TypeError (500) con firmas no ASCII."""
    payload = security.create_token(42).split(".")[0]
    assert security._decode_token(f"{payload}.firmañ") is None


@pytest.mark.limites
def test_token_vale_hasta_el_ultimo_segundo_de_su_vigencia(monkeypatch):
    inicio = 1_800_000_000
    monkeypatch.setattr(security.time, "time", lambda: inicio)
    token = security.create_token(7)
    vence = inicio + security.TOKEN_TTL_HOURS * 3600
    monkeypatch.setattr(security.time, "time", lambda: vence)
    assert security._decode_token(token) == 7
    monkeypatch.setattr(security.time, "time", lambda: vence + 1)
    assert security._decode_token(token) is None
