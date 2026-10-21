# language: es
@spec-002 @US-2
Característica: Registrar un agente y entregar su virtual key
  Como administrador quiero dar de alta un agente y entregarle su virtual key
  para que consuma modelos sin conocer las keys reales.

  Antecedentes:
    Dado que soy un usuario de governance con rol "admin"

  @CA-2.1
  Escenario: La key se entrega una sola vez con su guía de conexión
    Cuando registro el agente "Clasificador de Tickets" en el sistema "agentfactory"
    Entonces la respuesta tiene el código 201
    Y recibo una virtual key que empieza por "sk-"
    Y la guía de conexión incluye ejemplos para "python, java, curl"
    Y al consultar el agente no aparece la key

  @CA-2.2
  Escenario: Solo se guardan el alias y el hash de la key
    Cuando registro el agente "Clasificador de Tickets" en el sistema "agentfactory"
    Entonces el registro guardado tiene el alias "agentfactory/clasificador-de-tickets"
    Y el registro guardado no contiene la key en claro

  @CA-2.3
  Escenario: Regenerar la key invalida la anterior
    Dado que registré el agente "Clasificador de Tickets" en el sistema "agentfactory"
    Cuando regenero su key
    Entonces recibo una virtual key distinta a la anterior
    Y la key anterior ya no existe en el gateway

  @CA-2.4
  Escenario: Un usuario de solo lectura no puede registrar agentes
    Dado que soy un usuario de governance con rol "viewer"
    Cuando registro el agente "Agente Prohibido" en el sistema "agentfactory"
    Entonces la respuesta tiene el código 403
