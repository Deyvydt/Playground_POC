# language: es
@spec-002 @US-3
Característica: Presupuestos y límites por área y por agente

  Antecedentes:
    Dado que soy un usuario de governance con rol "admin"

  @CA-3.1
  Escenario: Jerarquía organización, área, sistema y agente
    Cuando registro el agente "Analizador de CV" en el sistema "talentia"
    Entonces el agente queda en el área "rrhh" y en el sistema "talentia"
    Y su key se emite para el team "rrhh" del gateway

  @CA-3.2
  Escenario: Cada key lleva modelos, presupuesto, periodo y límites
    Cuando registro el agente "Agente Limitado" en el sistema "agentfactory" con presupuesto 5 por "7d", 30 solicitudes y 10000 tokens por minuto
    Entonces el gateway recibió para su key el presupuesto 5, el periodo "7d", 30 solicitudes y 10000 tokens por minuto
    Y el gateway recibió los modelos "local-models"

  @CA-3.5
  Escenario: Cambiar los límites actualiza la key en el gateway
    Dado que registré el agente "Agente Ajustable" en el sistema "agentfactory"
    Cuando cambio su presupuesto a 3
    Entonces el gateway recibió para su key el presupuesto 3

  @CA-3.6
  Escenario: El área muestra su gasto frente a su presupuesto
    Dado que el gateway reporta para el team "desarrollo" un gasto de 2.5 de 10
    Cuando consulto las áreas
    Entonces el área "desarrollo" muestra un uso del 25%
