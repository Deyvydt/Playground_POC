# language: es
@spec-001 @US-1
Característica: Crear y configurar agentes
  Como desarrollador quiero crear y ajustar agentes
  para tener asistentes especializados sin programar.

  Antecedentes:
    Dado que inicié sesión como "desarrollador"

  @CA-1.1
  Escenario: Un agente nuevo aparece en el listado
    Cuando creo un agente "Clasificador de Correos" con las instrucciones "Clasifica correos por urgencia."
    Entonces la respuesta tiene el código 201
    Y el agente "Clasificador de Correos" aparece en el listado de agentes

  @CA-1.2
  Escenario: Editar las instrucciones cambia las respuestas siguientes
    Dado que existe un agente "Agente Editable" con las instrucciones "Responde en inglés."
    Cuando cambio las instrucciones de "Agente Editable" a "Responde siempre en español."
    Y le escribo "Hola" al agente "Agente Editable"
    Entonces el modelo recibió las instrucciones "Responde siempre en español."

  @CA-1.3
  Escenario: Un usuario de solo lectura no puede crear agentes
    Dado que inicié sesión como "solo lectura"
    Cuando creo un agente "Agente Prohibido" con las instrucciones "No debería existir."
    Entonces la respuesta tiene el código 403
    Y el agente "Agente Prohibido" no aparece en el listado de agentes
