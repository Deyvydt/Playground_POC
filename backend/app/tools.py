import ast
import operator
from datetime import datetime

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "calculadora",
            "description": "Evalua una expresion aritmetica y devuelve el resultado numerico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expresion": {"type": "string", "description": "Expresion matematica, ej: (120*3)/4"},
                },
                "required": ["expresion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fecha_actual",
            "description": "Devuelve la fecha y hora actual del servidor.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_ticket_interno",
            "description": "Busca el estado de un ticket interno de TCS Service Desk por su ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Identificador del ticket, ej: TCS-4471"},
                },
                "required": ["ticket_id"],
            },
        },
    },
]

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Expresion no permitida")


def calculadora(expresion: str) -> dict:
    try:
        tree = ast.parse(expresion, mode="eval")
        result = _safe_eval(tree)
        return {"expresion": expresion, "resultado": result}
    except Exception as exc:  # noqa: BLE001
        return {"expresion": expresion, "error": str(exc)}


def fecha_actual() -> dict:
    now = datetime.now()
    return {"fecha_iso": now.isoformat(), "legible": now.strftime("%A %d de %B de %Y, %H:%M")}


_MOCK_TICKETS = {
    "TCS-4471": {"estado": "En progreso", "prioridad": "Alta", "asignado_a": "Equipo de Infraestructura"},
    "TCS-1002": {"estado": "Resuelto", "prioridad": "Media", "asignado_a": "Mesa de Servicio"},
    "TCS-2090": {"estado": "Pendiente de aprobacion", "prioridad": "Baja", "asignado_a": "PMO"},
}


def consultar_ticket_interno(ticket_id: str) -> dict:
    ticket = _MOCK_TICKETS.get(ticket_id.upper())
    if not ticket:
        return {"ticket_id": ticket_id, "encontrado": False}
    return {"ticket_id": ticket_id.upper(), "encontrado": True, **ticket}


TOOL_IMPLEMENTATIONS = {
    "calculadora": lambda args: calculadora(**args),
    "fecha_actual": lambda args: fecha_actual(),
    "consultar_ticket_interno": lambda args: consultar_ticket_interno(**args),
}


def execute_tool(name: str, arguments: dict) -> dict:
    fn = TOOL_IMPLEMENTATIONS.get(name)
    if not fn:
        return {"error": f"Herramienta '{name}' no reconocida"}
    try:
        return fn(arguments or {})
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def definitions_for(names: list[str]) -> list[dict]:
    return [t for t in TOOL_DEFINITIONS if t["function"]["name"] in names]
