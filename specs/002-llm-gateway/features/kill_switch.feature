# language: es
@spec-002 @US-4
Característica: Kill switch y auto-pausa con aviso
  Como administrador quiero detener un agente al instante
  y que el sistema lo detenga solo si gasta de más o falla demasiado.

  Antecedentes:
    Dado que soy un usuario de governance con rol "admin"
    Y que registré el agente "Agente Vigilado" en el sistema "talentia"

  @CA-4.1
  Escenario: Pausar bloquea la key y reactivar la desbloquea
    Cuando pauso el agente con el motivo "Consumo anómalo"
    Entonces el agente queda "pausado" con el motivo "Consumo anómalo"
    Y su key está bloqueada en el gateway
    Cuando reactivo el agente
    Entonces el agente queda "activo"
    Y su key no está bloqueada en el gateway

  @CA-4.1
  Escenario: Un usuario de solo lectura no puede pausar
    Dado que soy un usuario de governance con rol "viewer"
    Cuando pauso el agente con el motivo "Intento sin permiso"
    Entonces la respuesta tiene el código 403
    Y su key no está bloqueada en el gateway

  @CA-4.2
  Escenario: Se pausa solo al superar su presupuesto
    Dado que el gateway reporta para el agente un gasto de 1.2 de 1.0
    Cuando corre el monitor
    Entonces el agente queda "pausado"
    Y hay un aviso "auto_pausa_gasto" de severidad "critical"

  @CA-4.2
  Escenario: Se pausa solo si la mayoría de sus llamadas recientes fallan
    Dado que el gateway reporta para el agente 6 llamadas recientes con 4 fallidas
    Cuando corre el monitor
    Entonces el agente queda "pausado"
    Y hay un aviso "auto_pausa_errores" de severidad "critical"

  @CA-4.2
  Escenario: Pocas fallas no pausan al agente
    Dado que el gateway reporta para el agente 6 llamadas recientes con 2 fallidas
    Cuando corre el monitor
    Entonces el agente queda "activo"

  @CA-4.3
  Escenario: Al llegar al 80% del presupuesto hay un aviso, una sola vez
    Dado que el gateway reporta para el agente un gasto de 0.85 de 1.0
    Cuando corre el monitor
    Y corre el monitor
    Entonces el agente queda "activo"
    Y hay exactamente 1 aviso "aviso_gasto"

  @CA-4.2 @CA-4.3
  Escenario: El aviso de presupuesto superado del gateway pausa al agente
    Cuando el gateway envía el aviso "budget_crossed" para la key del agente
    Entonces el agente queda "pausado"
    Y hay un aviso "auto_pausa_gasto" de severidad "critical"

  @CA-4.3
  Escenario: El webhook rechaza avisos sin el token correcto
    Cuando alguien envía un aviso al webhook con un token inválido
    Entonces la respuesta tiene el código 401
