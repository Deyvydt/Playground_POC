"""Contrato: ninguna solicitud generada desde el OpenAPI de agent-lab produce un 5xx."""
import schemathesis
from hypothesis import HealthCheck, settings
from schemathesis.checks import not_a_server_error

from app.main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app)


@schema.parametrize()
@settings(max_examples=15, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
def test_ninguna_solicitud_generada_produce_error_del_servidor(case):
    case.call_and_validate(headers={"Authorization": "Bearer rol:viewer"}, checks=[not_a_server_error])
