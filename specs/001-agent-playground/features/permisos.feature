# language: es
@spec-001 @US-6
Característica: Controlar accesos por rol
  Como administrador quiero que cada rol solo pueda hacer lo que le corresponde.

  @CA-6.1 @CA-6.2 @CA-6.3
  Esquema del escenario: Permisos por rol validados en el servidor
    Dado que inicié sesión como "<rol>"
    Cuando intento "<accion>"
    Entonces la acción es "<resultado>"

    Ejemplos:
      | rol           | accion                    | resultado |
      | solo lectura  | conversar con un agente   | permitida |
      | solo lectura  | crear un agente           | denegada  |
      | solo lectura  | ver la actividad reciente | denegada  |
      | desarrollador | ver la actividad reciente | permitida |
      | desarrollador | crear un agente           | permitida |
      | desarrollador | editar un agente          | permitida |
      | desarrollador | eliminar un agente        | denegada  |
      | desarrollador | crear un usuario          | denegada  |
      | administrador | eliminar un agente        | permitida |
      | administrador | crear un usuario          | permitida |

  @CA-6.4
  Escenario: Solo el administrador tiene el permiso de gobierno
    Entonces solo el rol "admin" tiene el permiso "govern"
