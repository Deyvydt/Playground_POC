# language: es
@spec-001 @US-7
Característica: Iniciar sesión y administrar usuarios
  Como administrador quiero controlar quién entra y con qué rol.

  @CA-7.1
  Escenario: Solo se entra con correo y contraseña válidos
    Cuando inicio sesión con "ana.rios@tcs.com" y la contraseña "Tcs2026!"
    Entonces la respuesta tiene el código 200
    Y recibo un token de sesión
    Cuando inicio sesión con "ana.rios@tcs.com" y la contraseña "incorrecta"
    Entonces la respuesta tiene el código 401

  @CA-7.1
  Escenario: Las contraseñas no se guardan en texto plano
    Entonces ninguna contraseña guardada coincide con el texto "Tcs2026!"

  @CA-7.2
  Escenario: El administrador crea una cuenta con rol y contraseña temporal
    Dado que inicié sesión como "administrador"
    Cuando creo el usuario "nuevo.dev@tcs.com" con el rol "developer" y la contraseña "Temporal1"
    Entonces la respuesta tiene el código 201
    Y "nuevo.dev@tcs.com" puede iniciar sesión con "Temporal1"

  @CA-7.3
  Escenario: Una cuenta desactivada no puede iniciar sesión
    Dado que inicié sesión como "administrador"
    Cuando desactivo la cuenta de "carlos.vega@tcs.com"
    E inicio sesión con "carlos.vega@tcs.com" y la contraseña "Tcs2026!"
    Entonces la respuesta tiene el código 403

  @CA-7.4
  Escenario: Los permisos se validan en el servidor
    Dado que inicié sesión como "solo lectura"
    Cuando creo el usuario "intruso@tcs.com" con el rol "admin" y la contraseña "Intruso1"
    Entonces la respuesta tiene el código 403
