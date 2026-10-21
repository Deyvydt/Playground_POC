"""Contrato: Schemathesis genera solicitudes desde el OpenAPI del backend y ninguna debe producir un 5xx.

Solo se exige `not_a_server_error`: FastAPI no documenta los 401/403/404/409 de cada ruta,
así que exigir conformidad de códigos daría falsos positivos.
"""
import schemathesis
from hypothesis import HealthCheck, settings
from schemathesis.checks import not_a_server_error

from app.main import app
from support import auth_headers

schema = schemathesis.openapi.from_asgi("/openapi.json", app)


@schema.parametrize()
@settings(max_examples=15, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
def test_ninguna_solicitud_generada_produce_error_del_servidor(case):
    case.call_and_validate(headers=auth_headers("admin"), checks=[not_a_server_error])
