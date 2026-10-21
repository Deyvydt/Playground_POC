# language: es
@spec-001 @US-4
Característica: Orquestar varios agentes en un flujo
  Como analista quiero encadenar agentes
  para resolver una tarea de varios pasos.

  Antecedentes:
    Dado que inicié sesión como "solo lectura"

  @CA-4.1 @CA-4.2 @CA-4.3
  Escenario: Cada paso usa la salida del anterior y el resultado final es el del último agente
    Dado que el modelo responderá "Ventas subieron 12%."
    Y que luego el modelo responderá "Informe: las ventas crecieron 12% este trimestre."
    Cuando ejecuto un flujo con "Analista de Datos, Redactor de Reportes" y la entrada "Analiza las ventas"
    Entonces el flujo tiene 2 pasos en el orden "Analista de Datos, Redactor de Reportes"
    Y el segundo paso recibió la salida del primero
    Y el resultado final es "Informe: las ventas crecieron 12% este trimestre."

  @CA-4.2
  Escenario: El flujo en vivo informa cada paso a medida que termina
    Cuando ejecuto en vivo un flujo con "Analista de Datos, Redactor de Reportes" y la entrada "Analiza las ventas"
    Entonces los eventos recibidos son "start, step, start, step, done"
