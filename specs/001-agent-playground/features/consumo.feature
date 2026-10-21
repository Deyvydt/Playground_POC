# language: es
@spec-001 @US-5
Característica: Monitorear consumo y actividad
  Como líder quiero ver el consumo de los agentes
  para entender el uso y el ahorro frente a la nube.

  @CA-5.1
  Escenario: El panel suma solicitudes y tokens de cada conversación
    Dado que inicié sesión como "desarrollador"
    Y que conversé 3 veces con el agente "Soporte TI"
    Cuando consulto el resumen de consumo de los últimos 30 días
    Entonces el resumen reporta 3 solicitudes
    Y el resumen reporta 45 tokens en total
    Y el desglose por agente muestra 3 solicitudes para "Soporte TI"

  @CA-5.2
  Escenario: El costo local es cero y se compara con una referencia de la nube
    Dado que inicié sesión como "desarrollador"
    Y que conversé 2 veces con el agente "Soporte TI"
    Cuando consulto el resumen de consumo de los últimos 30 días
    Entonces el costo local es 0
    Y el costo estimado en la nube es mayor que 0
