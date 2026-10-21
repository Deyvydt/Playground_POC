"""Pasos Gherkin del backend (spec 001 y spec 002 US-7). Los .feature viven en specs/<feature>/features/."""
import json

import httpx
import pytest
from pytest_bdd import given, parsers, then, when
from sqlmodel import Session, select

from app import gateway_keys, ollama_client, security
from app.database import engine
from app.models import Agent, KnowledgeChunk, KnowledgeDocument, User
from support import ORIGINALS, agent_by_name, auth_headers

ACCIONES = {
    "conversar con un agente": ("post", "/api/agents/1/chat", {"message": "Hola"}),
    "crear un agente": ("post", "/api/agents", {"name": "Agente de Permisos", "role_prompt": "Prueba de permisos."}),
    "editar un agente": ("put", "/api/agents/2", {"description": "Editado en prueba"}),
    "eliminar un agente": ("delete", "/api/agents/6", None),
    "crear un usuario": ("post", "/api/users", {"name": "Usuario Permisos", "email": "permisos@tcs.com", "password": "Clave123"}),
    "ver la actividad reciente": ("get", "/api/metrics/activity", None),
}


@pytest.fixture
def ctx():
    return {"headers": {}}


def _send(client, ctx, method, path, payload=None, **kwargs):
    kwargs.setdefault("headers", ctx["headers"])
    if payload is not None:
        kwargs["json"] = payload
    ctx["response"] = getattr(client, method)(path, **kwargs)
    return ctx["response"]


# --- Dado ---------------------------------------------------------------------------------

@given(parsers.parse('que inicié sesión como "{rol}"'))
def sesion(ctx, rol):
    ctx["headers"] = auth_headers(rol)


@given(parsers.parse('que existe un agente "{nombre}" con las instrucciones "{prompt}"'))
def existe_agente(client, nombre, prompt):
    client.post("/api/agents", json={"name": nombre, "role_prompt": prompt}, headers=auth_headers("admin"))


@given(parsers.parse('que el modelo responderá "{texto}"'))
@given(parsers.parse('que luego el modelo responderá "{texto}"'))
def modelo_respondera(fake_llm, texto):
    fake_llm.reply(texto)


@given(parsers.parse('que el modelo pedirá la herramienta "{herramienta}" con {argumentos}'))
def modelo_pide_herramienta(fake_llm, herramienta, argumentos):
    fake_llm.tool_call(herramienta, json.loads(argumentos))


@given("que el motor de modelos no está disponible")
def motor_caido(fake_llm):
    fake_llm.failure = "El motor de modelos no está disponible"


@given(parsers.parse('que conversé {veces:d} veces con el agente "{nombre}"'))
def conversaciones_previas(client, ctx, veces, nombre):
    agent_id = agent_by_name(nombre).id
    for i in range(veces):
        client.post(f"/api/agents/{agent_id}/chat", json={"message": f"consulta {i}"}, headers=ctx["headers"])


@given(parsers.parse('que el backend usa el gateway y el agente "{nombre}" tiene la virtual key "{key}"'))
def backend_con_gateway(ctx, monkeypatch, nombre, key):
    gateway = {"requests": [], "status": 200}
    real_client = httpx.AsyncClient

    def responder(request):
        gateway["requests"].append(request)
        if gateway["status"] != 200:
            return httpx.Response(gateway["status"], json={"error": "rechazado"})
        return httpx.Response(200, json={
            "choices": [{"message": {"role": "assistant", "content": "Hola, soy Soporte TI."}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 6},
        })

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(responder)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(ollama_client.httpx, "AsyncClient", client_factory)
    monkeypatch.setattr(ollama_client, "chat", ORIGINALS["chat"])
    monkeypatch.setattr(ollama_client, "LLM_GATEWAY_URL", "http://gateway.test")
    monkeypatch.setattr(gateway_keys, "LLM_GATEWAY_URL", "http://gateway.test")
    with Session(engine) as session:
        agent = session.get(Agent, agent_by_name(nombre).id)
        agent.gateway_key_enc = gateway_keys.encrypt(key)
        session.add(agent)
        session.commit()
    ctx["gateway"] = gateway


@given(parsers.parse("que el gateway rechaza al agente con el código {status:d}"))
def gateway_rechaza(ctx, status):
    ctx["gateway"]["status"] = status


# --- Cuando -------------------------------------------------------------------------------

@when(parsers.parse('creo un agente "{nombre}" con las instrucciones "{prompt}"'))
def crear_agente(client, ctx, nombre, prompt):
    _send(client, ctx, "post", "/api/agents", {"name": nombre, "role_prompt": prompt})


@when(parsers.parse('cambio las instrucciones de "{nombre}" a "{prompt}"'))
def cambiar_instrucciones(client, ctx, nombre, prompt):
    _send(client, ctx, "put", f"/api/agents/{agent_by_name(nombre).id}", {"role_prompt": prompt})


@when(parsers.parse('le escribo "{mensaje}" al agente "{nombre}"'))
def escribir(client, ctx, mensaje, nombre):
    _send(client, ctx, "post", f"/api/agents/{agent_by_name(nombre).id}/chat", {"message": mensaje})


@when(parsers.parse('subo el documento "{archivo}" al agente "{nombre}" con el texto:'))
def subir_documento(client, ctx, archivo, nombre, docstring):
    _send(client, ctx, "post", f"/api/agents/{agent_by_name(nombre).id}/knowledge",
          files={"file": (archivo, docstring.encode())})


def _pipeline(nombres: str) -> list[int]:
    return [agent_by_name(n.strip()).id for n in nombres.split(",")]


@when(parsers.parse('ejecuto un flujo con "{agentes}" y la entrada "{texto}"'))
def ejecutar_flujo(client, ctx, agentes, texto):
    _send(client, ctx, "post", "/api/orchestration/run", {"input_text": texto, "pipeline": _pipeline(agentes)})


@when(parsers.parse('ejecuto en vivo un flujo con "{agentes}" y la entrada "{texto}"'))
def ejecutar_flujo_vivo(client, ctx, agentes, texto):
    _send(client, ctx, "post", "/api/orchestration/stream", {"input_text": texto, "pipeline": _pipeline(agentes)})


@when(parsers.parse("consulto el resumen de consumo de los últimos {dias:d} días"))
def consultar_resumen(client, ctx, dias):
    _send(client, ctx, "get", f"/api/metrics/summary?days={dias}")


@when(parsers.parse('inicio sesión con "{email}" y la contraseña "{password}"'))
def iniciar_sesion(client, ctx, email, password):
    _send(client, ctx, "post", "/api/auth/login", {"email": email, "password": password}, headers={})


@when(parsers.parse('creo el usuario "{email}" con el rol "{rol}" y la contraseña "{password}"'))
def crear_usuario(client, ctx, email, rol, password):
    _send(client, ctx, "post", "/api/users", {"name": "Usuario de Prueba", "email": email, "role": rol, "password": password})


@when(parsers.parse('desactivo la cuenta de "{email}"'))
def desactivar(client, ctx, email):
    with Session(engine) as session:
        user_id = session.exec(select(User).where(User.email == email)).one().id
    _send(client, ctx, "put", f"/api/users/{user_id}", {"is_active": False})


@when(parsers.parse('intento "{accion}"'))
def intentar(client, ctx, accion):
    method, path, payload = ACCIONES[accion]
    _send(client, ctx, method, path, payload)


# --- Entonces -----------------------------------------------------------------------------

@then(parsers.parse("la respuesta tiene el código {codigo:d}"))
def codigo(ctx, codigo):
    assert ctx["response"].status_code == codigo, ctx["response"].text


@then(parsers.parse('el agente "{nombre}" aparece en el listado de agentes'))
def aparece(client, nombre):
    assert nombre in [a["name"] for a in client.get("/api/agents", headers=auth_headers("viewer")).json()]


@then(parsers.parse('el agente "{nombre}" no aparece en el listado de agentes'))
def no_aparece(client, nombre):
    assert nombre not in [a["name"] for a in client.get("/api/agents", headers=auth_headers("viewer")).json()]


@then(parsers.parse('el modelo recibió las instrucciones "{prompt}"'))
def recibio_instrucciones(fake_llm, prompt):
    assert fake_llm.last_system_prompt == prompt


@then(parsers.parse('la respuesta del agente es "{texto}"'))
def respuesta_agente(ctx, texto):
    assert ctx["response"].json()["message"]["content"] == texto


@then(parsers.parse("la conversación guarda {n:d} mensajes"))
def mensajes_guardados(client, ctx, n):
    conv = ctx["response"].json()["conversation_id"]
    assert len(client.get(f"/api/conversations/{conv}/messages", headers=ctx["headers"]).json()) == n


@then(parsers.parse('la traza tiene los pasos "{pasos}" en ese orden'))
def pasos_traza(ctx, pasos):
    assert [s["type"] for s in ctx["response"].json()["trace"]] == [p.strip() for p in pasos.split(",")]


@then(parsers.parse('la traza incluye la herramienta "{herramienta}" con resultado {valor:d}'))
def traza_herramienta(ctx, herramienta, valor):
    paso = next(s for s in ctx["response"].json()["trace"] if s["type"] == "tool_call")
    assert paso["title"] == f"Herramienta: {herramienta}"
    assert paso["detail"]["argumentos"] and paso["detail"]["resultado"]["resultado"] == valor


@then(parsers.parse("el consumo registra {n:d} solicitud fallida"))
def consumo_fallido(client, n):
    resumen = client.get("/api/metrics/summary", headers=auth_headers("admin")).json()
    assert sum(r["errors"] for r in resumen["agents_breakdown"]) == n


@then(parsers.parse('el agente "{nombre}" tiene {docs:d} documento con al menos {fragmentos:d} fragmento'))
def documentos_indexados(nombre, docs, fragmentos):
    agent_id = agent_by_name(nombre).id
    with Session(engine) as session:
        documentos = session.exec(select(KnowledgeDocument).where(KnowledgeDocument.agent_id == agent_id)).all()
        chunks = session.exec(select(KnowledgeChunk).where(KnowledgeChunk.agent_id == agent_id)).all()
    assert len(documentos) == docs
    assert len(chunks) >= fragmentos and all(c.embedding for c in chunks)


@then(parsers.parse('la traza incluye un paso de recuperación cuyo primer fragmento menciona "{palabra}"'))
def traza_recuperacion(ctx, palabra):
    paso = ctx["response"].json()["trace"][0]
    assert paso["type"] == "retrieval"
    assert palabra in paso["detail"][0]["preview"].lower()


@then("el modelo recibió el contexto recuperado en sus instrucciones")
def contexto_en_prompt(fake_llm):
    assert "[Fragmento 1]" in fake_llm.last_system_prompt


@then(parsers.parse('el flujo tiene {n:d} pasos en el orden "{agentes}"'))
def pasos_flujo(ctx, n, agentes):
    pasos = ctx["response"].json()["steps"]
    assert [p["agent_name"] for p in pasos] == [a.strip() for a in agentes.split(",")]
    assert len(pasos) == n


@then("el segundo paso recibió la salida del primero")
def segundo_recibe_salida(ctx, fake_llm):
    salida_primero = ctx["response"].json()["steps"][0]["output"]
    assert salida_primero in fake_llm.calls[-1]["messages"][-1]["content"]


@then(parsers.parse('el resultado final es "{texto}"'))
def resultado_final(ctx, texto):
    assert ctx["response"].json()["final_output"] == texto


@then(parsers.parse('los eventos recibidos son "{eventos}"'))
def eventos_flujo(ctx, eventos):
    recibidos = [json.loads(line)["event"] for line in ctx["response"].text.splitlines() if line]
    assert recibidos == [e.strip() for e in eventos.split(",")]


@then(parsers.parse("el resumen reporta {n:d} solicitudes"))
def resumen_solicitudes(ctx, n):
    assert ctx["response"].json()["total_requests"] == n


@then(parsers.parse("el resumen reporta {n:d} tokens en total"))
def resumen_tokens(ctx, n):
    assert ctx["response"].json()["total_tokens"] == n


@then(parsers.parse('el desglose por agente muestra {n:d} solicitudes para "{nombre}"'))
def desglose_agente(ctx, n, nombre):
    fila = next(r for r in ctx["response"].json()["agents_breakdown"] if r["agent_name"] == nombre)
    assert fila["requests"] == n


@then("el costo local es 0")
def costo_local(ctx):
    assert ctx["response"].json()["local_cost_usd"] == 0


@then("el costo estimado en la nube es mayor que 0")
def costo_nube(ctx):
    assert ctx["response"].json()["estimated_cloud_cost_usd"] > 0


@then("recibo un token de sesión")
def token_recibido(client, ctx):
    token = ctx["response"].json()["token"]
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200


@then(parsers.parse('ninguna contraseña guardada coincide con el texto "{texto}"'))
def contrasenas_hasheadas(texto):
    with Session(engine) as session:
        hashes = [u.password_hash for u in session.exec(select(User)).all()]
    assert hashes and all(texto not in h and security.verify_password(texto, h) for h in hashes)


@then(parsers.parse('"{email}" puede iniciar sesión con "{password}"'))
def puede_entrar(client, email, password):
    assert client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 200


@then(parsers.parse('la acción es "{resultado}"'))
def accion_resultado(ctx, resultado):
    status = ctx["response"].status_code
    if resultado == "permitida":
        assert status < 400, ctx["response"].text
    else:
        assert status == 403, ctx["response"].text


@then(parsers.parse('solo el rol "{rol}" tiene el permiso "{permiso}"'))
def permiso_exclusivo(rol, permiso):
    assert [r for r, perms in security.PERMISSIONS.items() if permiso in perms] == [rol]


@then(parsers.parse('el gateway recibió la key "{key}"'))
def gateway_key(ctx, key):
    assert {r.headers["Authorization"] for r in ctx["gateway"]["requests"]} == {f"Bearer {key}"}


@then(parsers.parse('el gateway recibió metadatos con los tags "{tags}"'))
def gateway_tags(ctx, tags):
    body = json.loads(ctx["gateway"]["requests"][-1].content)
    assert body["metadata"]["tags"] == [t.strip() for t in tags.split(",")]
    assert body["metadata"]["session_id"] == f"conversacion-{ctx['response'].json()['conversation_id']}"


@then(parsers.parse('el detalle del error es "{detalle}"'))
def detalle_error(ctx, detalle):
    assert ctx["response"].json()["detail"] == detalle
