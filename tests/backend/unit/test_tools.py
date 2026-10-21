import pytest

from app import tools


@pytest.mark.particion
@pytest.mark.particion
@pytest.mark.adivinanza_errores
@pytest.mark.particion
@pytest.mark.parametrize("expresion, esperado", [
    ("2+3", 5),
    ("(120*3)/4", 90),
    ("2**10", 1024),
    ("-5 + 2", -3),
    ("17 % 5", 2),
    ("1.5 * 4", 6.0),
])
def test_calculadora_resuelve_operaciones_aritmeticas(expresion, esperado):
    assert tools.calculadora(expresion)["resultado"] == esperado


@pytest.mark.parametrize("expresion", [
    "__import__('os').system('echo hola')",
    "open('/etc/passwd').read()",
    "abs(-3)",
    "[1, 2, 3]",
    "x + 1",
])
def test_calculadora_rechaza_codigo_que_no_es_aritmetica(expresion):
    resultado = tools.calculadora(expresion)
    assert "error" in resultado
    assert "resultado" not in resultado


@pytest.mark.adivinanza_errores
def test_calculadora_informa_division_por_cero():
    assert "error" in tools.calculadora("1/0")


def test_fecha_actual_devuelve_formato_iso_y_legible():
    resultado = tools.fecha_actual()
    assert set(resultado) == {"fecha_iso", "legible"}
    assert "T" in resultado["fecha_iso"]


@pytest.mark.parametrize("ticket", ["TCS-4471", "tcs-4471"])
def test_consultar_ticket_encuentra_tickets_sin_importar_mayusculas(ticket):
    resultado = tools.consultar_ticket_interno(ticket)
    assert resultado["encontrado"] is True
    assert resultado["ticket_id"] == "TCS-4471"
    assert resultado["estado"] == "En progreso"


@pytest.mark.particion
def test_consultar_ticket_inexistente_no_inventa_datos():
    assert tools.consultar_ticket_interno("TCS-0000") == {"ticket_id": "TCS-0000", "encontrado": False}


@pytest.mark.particion
def test_execute_tool_con_herramienta_desconocida_devuelve_error():
    assert "no reconocida" in tools.execute_tool("borrar_todo", {})["error"]


@pytest.mark.adivinanza_errores
def test_execute_tool_con_argumentos_invalidos_devuelve_error_sin_excepcion():
    assert "error" in tools.execute_tool("calculadora", {"otro": "1+1"})


def test_definitions_for_filtra_solo_las_herramientas_pedidas():
    nombres = [d["function"]["name"] for d in tools.definitions_for(["calculadora", "inexistente"])]
    assert nombres == ["calculadora"]


def test_catalogo_de_herramientas_tiene_implementacion_para_cada_definicion():
    definidas = {d["function"]["name"] for d in tools.TOOL_DEFINITIONS}
    assert definidas == set(tools.TOOL_IMPLEMENTATIONS)
