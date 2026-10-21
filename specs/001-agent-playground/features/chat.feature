# language: es
@spec-001 @US-2
Característica: Conversar con un agente y ver su razonamiento
  Como usuario quiero conversar con un agente y ver cada paso que siguió
  para confiar en su respuesta.

  Antecedentes:
    Dado que inicié sesión como "solo lectura"

  @CA-2.1
  Escenario: El agente responde y la conversación queda guardada
    Dado que el modelo responderá "Tu ticket está en progreso."
    Cuando le escribo "¿Cómo va mi ticket?" al agente "Soporte TI"
    Entonces la respuesta tiene el código 200
    Y la respuesta del agente es "Tu ticket está en progreso."
    Y la conversación guarda 2 mensajes

  @CA-2.2
  Escenario: La traza muestra los pasos en orden
    Cuando le escribo "Resume este texto" al agente "Redactor de Reportes"
    Entonces la traza tiene los pasos "system_prompt, model_call, final_answer" en ese orden

  @CA-2.3
  Escenario: La traza muestra la herramienta usada con su argumento y resultado
    Dado que el modelo pedirá la herramienta "calculadora" con {"expresion": "(120*3)/4"}
    Y que luego el modelo responderá "El resultado es 90."
    Cuando le escribo "¿Cuánto es (120*3)/4?" al agente "Analista de Datos"
    Entonces la traza incluye la herramienta "calculadora" con resultado 90
    Y la respuesta del agente es "El resultado es 90."

  @CA-2.4
  Escenario: Si el motor de modelos no responde, el error es claro y queda registrado
    Dado que el motor de modelos no está disponible
    Cuando le escribo "Hola" al agente "Soporte TI"
    Entonces la respuesta tiene el código 503
    Y el consumo registra 1 solicitud fallida
