# language: es
@spec-002 @US-6
Característica: Agentes de prueba LangGraph
  Como desarrollador quiero ejecutar los grafos de Talentia y AgentFactory
  para validar el gobierno sin depender de los sistemas reales.

  @CA-6.1
  Escenario: Un candidato con buen puntaje pasa a entrevista
    Dado que el nodo "evaluador_ajuste" responderá "85"
    Cuando ejecuto el grafo "talentia" con un CV y una vacante
    Entonces el recorrido fue "analizador_cv, evaluador_ajuste, generador_entrevista"
    Y el resultado incluye el puntaje 85

  @CA-6.1
  Escenario: Un candidato con puntaje bajo recibe un mensaje de rechazo
    Dado que el nodo "evaluador_ajuste" responderá "40"
    Cuando ejecuto el grafo "talentia" con un CV y una vacante
    Entonces el recorrido fue "analizador_cv, evaluador_ajuste, redactor_comunicaciones"

  @CA-6.2
  Escenario: El código con observaciones vuelve a generarse antes de los tests
    Dado que el nodo "revisor_codigo" responderá "OBSERVACIONES: falta validar la moneda" y luego "OBSERVACIONES: ninguna"
    Cuando ejecuto el grafo "agentfactory" con un requerimiento
    Entonces el recorrido fue "generador_codigo, revisor_codigo, generador_codigo, revisor_codigo, generador_tests, documentador"

  @CA-6.3
  Escenario: Cada nodo llama al modelo con su propia virtual key
    Cuando ejecuto el grafo "talentia" con un CV y una vacante
    Entonces cada nodo usó una virtual key distinta
    Y cada llamada llevó el identificador de la ejecución como traza

  @CA-6.4
  Escenario: Si un nodo está pausado el grafo se detiene con un mensaje claro
    Dado que el nodo "evaluador_ajuste" está pausado en el gateway
    Cuando ejecuto el grafo "talentia" con un CV y una vacante
    Entonces el grafo se detuvo con el mensaje "El agente está pausado por un administrador."
    Y el recorrido fue "analizador_cv, evaluador_ajuste"
