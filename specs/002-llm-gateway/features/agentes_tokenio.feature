# language: es
@spec-002 @US-7
Característica: Agentes de TokenIO bajo gobierno
  Los agentes propios de TokenIO consumen modelos a través del gateway
  con su virtual key, sin cambiar su comportamiento.

  Antecedentes:
    Dado que el backend usa el gateway y el agente "Soporte TI" tiene la virtual key "sk-agente-soporte"
    Y que inicié sesión como "solo lectura"

  @CA-7.1
  Escenario: El chat llama al gateway con la key del agente y la traza de la conversación
    Cuando le escribo "Hola" al agente "Soporte TI"
    Entonces la respuesta tiene el código 200
    Y el gateway recibió la key "sk-agente-soporte"
    Y el gateway recibió metadatos con los tags "agent:Soporte TI, area:plataforma, sistema:tokenio"

  @CA-7.2
  Escenario: Si el agente está pausado en el gateway el chat lo explica
    Dado que el gateway rechaza al agente con el código 401
    Cuando le escribo "Hola" al agente "Soporte TI"
    Entonces la respuesta tiene el código 503
    Y el detalle del error es "El agente está pausado por un administrador."

  @CA-7.2
  Escenario: Si el agente agotó su presupuesto el chat lo explica
    Dado que el gateway rechaza al agente con el código 422
    Cuando le escribo "Hola" al agente "Soporte TI"
    Entonces la respuesta tiene el código 503
    Y el detalle del error es "El agente agotó su presupuesto o límite de uso."
