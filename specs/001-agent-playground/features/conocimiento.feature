# language: es
@spec-001 @US-3
Característica: Responder con conocimiento interno
  Como responsable de un área quiero cargar documentos a un agente
  para que responda con información propia de TCS.

  Antecedentes:
    Dado que inicié sesión como "desarrollador"

  @CA-3.1
  Escenario: Un documento cargado se fragmenta e indexa
    Cuando subo el documento "politicas.txt" al agente "Asistente de RR.HH." con el texto:
      """
      Politica de teletrabajo: los colaboradores pueden trabajar remoto dos dias por semana.
      Politica de reembolsos: los gastos de viaje se reembolsan en un plazo de 15 dias.
      """
    Entonces la respuesta tiene el código 201
    Y el agente "Asistente de RR.HH." tiene 1 documento con al menos 1 fragmento

  @CA-3.2
  Escenario: La pregunta usa el fragmento más relevante del manual
    Cuando le escribo "¿Cuántos días de vacaciones acumulo por mes?" al agente "Asesor de Onboarding"
    Entonces la traza incluye un paso de recuperación cuyo primer fragmento menciona "vacaciones"
    Y el modelo recibió el contexto recuperado en sus instrucciones

  @CA-3.4
  Esquema del escenario: Solo se aceptan formatos de texto soportados
    Cuando subo el documento "<archivo>" al agente "Asistente de RR.HH." con el texto:
      """
      contenido de prueba
      """
    Entonces la respuesta tiene el código <codigo>

    Ejemplos:
      | archivo      | codigo |
      | notas.md     | 201    |
      | planilla.xls | 400    |
      | imagen.png   | 400    |
