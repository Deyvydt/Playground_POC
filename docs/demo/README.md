# Video demo de TokenIO

[`tokenio-demo.mp4`](tokenio-demo.mp4) (~3 min, 1280×720) recorre lo probado:

1. Inicio de sesión (administradora).
2. Agente de Soporte TI con herramienta (consulta de ticket) y su traza.
3. Asesor de Onboarding respondiendo con el manual interno y su traza.
4. Gobierno: gasto por área y por agente.
5. Registro de un agente de otro sistema (Cobranzas) con presupuesto y emisión de su key virtual.
6. El sistema externo llama a la IA a través del gateway con esa key.
7. Su consumo aparece en TokenIO: tokens, latencia, costo por llamada.
8. Pausa (kill switch): la siguiente llamada del sistema externo recibe 401.
9. Avisos de gobierno y reactivación: el sistema externo vuelve a funcionar.
10. Laboratorio: grafo Talentia (4 agentes, cada uno con su key).
11. Consumo general.

Todos los servicios corrieron de verdad (gateway LiteLLM + Postgres, governance, backend,
agent-lab y frontend). Solo el modelo fue un doble OpenAI-compatible con respuestas fijas,
porque el entorno de grabación no tenía GPU ni Ollama; por eso los costos son de demostración.
