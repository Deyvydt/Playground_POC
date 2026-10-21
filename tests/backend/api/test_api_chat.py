def chat(client, headers, agent_id, message, conversation_id=None):
    payload = {"message": message, **({"conversation_id": conversation_id} if conversation_id else {})}
    return client.post(f"/api/agents/{agent_id}/chat", json=payload, headers=headers)


def test_chat_crea_una_conversacion_con_titulo_del_primer_mensaje(client, as_role):
    viewer = as_role("viewer")
    r = chat(client, viewer, 1, "¿Cómo reinicio mi VPN?")
    assert r.status_code == 200
    conversaciones = client.get("/api/agents/1/conversations", headers=viewer).json()
    assert conversaciones[0]["id"] == r.json()["conversation_id"]
    assert conversaciones[0]["title"] == "¿Cómo reinicio mi VPN?"


def test_continuar_la_conversacion_envia_el_historial_al_modelo(client, as_role, fake_llm):
    viewer = as_role("viewer")
    fake_llm.reply("Primera respuesta.")
    conv = chat(client, viewer, 1, "Primera pregunta").json()["conversation_id"]
    chat(client, viewer, 1, "Segunda pregunta", conv)
    mensajes = fake_llm.calls[-1]["messages"]
    assert [m["content"] for m in mensajes[1:]] == ["Primera pregunta", "Primera respuesta.", "Segunda pregunta"]
    assert len(client.get(f"/api/conversations/{conv}/messages", headers=viewer).json()) == 4


def test_los_mensajes_guardan_la_traza_y_los_tokens(client, as_role):
    viewer = as_role("viewer")
    conv = chat(client, viewer, 3, "Resume").json()["conversation_id"]
    respuesta = client.get(f"/api/conversations/{conv}/messages", headers=viewer).json()[-1]
    assert respuesta["role"] == "assistant"
    assert respuesta["trace"][-1]["type"] == "final_answer"
    assert (respuesta["prompt_tokens"], respuesta["completion_tokens"]) == (10, 5)


def test_un_usuario_no_ve_las_conversaciones_de_otro_pero_el_admin_si(client, as_role):
    conv = chat(client, as_role("viewer"), 1, "Privado").json()["conversation_id"]
    assert client.get(f"/api/conversations/{conv}/messages", headers=as_role("developer")).status_code == 404
    assert chat(client, as_role("developer"), 1, "Intruso", conv).status_code == 404
    assert client.get(f"/api/conversations/{conv}/messages", headers=as_role("admin")).status_code == 200
    assert client.get("/api/agents/1/conversations", headers=as_role("developer")).json() == []


def test_eliminar_una_conversacion_borra_sus_mensajes(client, as_role):
    viewer = as_role("viewer")
    conv = chat(client, viewer, 1, "Borrar").json()["conversation_id"]
    assert client.delete(f"/api/conversations/{conv}", headers=viewer).json() == {"ok": True}
    assert client.get(f"/api/conversations/{conv}/messages", headers=viewer).status_code == 404


def test_un_agente_inactivo_no_conversa(client, as_role):
    client.put("/api/agents/1", json={"status": "inactive"}, headers=as_role("admin"))
    r = chat(client, as_role("viewer"), 1, "Hola")
    assert r.status_code == 409 and r.json()["detail"] == "Este agente está pausado"


def test_chat_con_agente_inexistente_responde_404(client, as_role):
    assert chat(client, as_role("viewer"), 999, "Hola").status_code == 404


def test_mensaje_vacio_es_rechazado(client, as_role):
    assert chat(client, as_role("viewer"), 1, "").status_code == 422


def test_falla_del_motor_responde_503_con_el_motivo(client, as_role, fake_llm):
    fake_llm.failure = "El motor de modelos no está disponible"
    r = chat(client, as_role("viewer"), 1, "Hola")
    assert r.status_code == 503 and r.json()["detail"] == "El motor de modelos no está disponible"


def test_el_chat_agrupa_su_traza_por_conversacion(client, as_role, fake_llm):
    conv = chat(client, as_role("viewer"), 3, "Hola").json()["conversation_id"]
    meta = fake_llm.calls[-1]["metadata"]
    assert meta["session_id"] == f"conversacion-{conv}"
    assert meta["trace_name"] == "chat · Redactor de Reportes"
