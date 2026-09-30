# Especificación de Funcionalidad: TCS Agent Playground

**Feature branch**: `001-agent-playground`
**Creado**: 2026-09-30
**Estado**: Borrador para revisión de negocio (POC)
**Entrada**: "Un playground propio para administrar agentes internos de TCS: crear,
probar, monitorear y gestionar agentes de IA de forma centralizada, con modelos
locales, RAG, herramientas, trazabilidad y control de accesos."

## Resumen Ejecutivo

TCS necesita evaluar si conviene construir un entorno propio para administrar
agentes de IA en lugar de depender de playgrounds públicos de terceros. Este POC
demuestra, con funcionalidad real (no solo mockups), las cuatro capacidades clave
que tal plataforma debería tener, para que la Gerencia Regional pueda decidir si
se invierte en una versión productiva.

## Usuarios y Roles

| Rol | Necesidad principal |
|---|---|
| Administrador (ej. Gerente Regional) | Ver el panorama completo: costos, uso, agentes activos; decidir si el POC pasa a producción. |
| Desarrollador / AI Engineer | Crear y configurar agentes, conectar bases de conocimiento, depurar su comportamiento. |
| Usuario de negocio (solo lectura) | Usar agentes ya creados para resolver tareas puntuales, sin tocar su configuración. |

## Historias de Usuario (por prioridad)

### US-1 — Crear y configurar un agente (Prioridad: P1)
Como Desarrollador, quiero definir el rol (prompt de sistema), el modelo y las
herramientas de un agente, para adaptarlo a una necesidad interna específica sin
escribir código.

**Criterios de aceptación**:
1. Dado que estoy en "Agentes", cuando presiono "Nuevo agente" y completo nombre,
   prompt de sistema, modelo y herramientas, entonces el agente queda disponible
   de inmediato en el playground.
2. Dado un agente existente, cuando edito su prompt o modelo, entonces sus
   próximas conversaciones usan la nueva configuración.
3. Un usuario con rol "solo lectura" NO puede ver el botón de creación/edición.

### US-2 — Conversar con un agente y ver su razonamiento (Prioridad: P1)
Como cualquier usuario autorizado, quiero chatear con un agente y ver qué hizo
internamente (prompt usado, contexto recuperado, herramientas invocadas), para
confiar en su respuesta y poder depurarla.

**Criterios de aceptación**:
1. Al enviar un mensaje, recibo una respuesta generada por un modelo local
   (Ollama), no simulada.
2. Puedo expandir una "traza" que muestra, en orden, cada paso de razonamiento.
3. Si el agente usa una herramienta (ej. calculadora), veo el argumento enviado
   y el resultado devuelto.

### US-3 — Responder con conocimiento interno (RAG) (Prioridad: P1)
Como Desarrollador, quiero subir un documento interno (manual, PDF, texto) a un
agente, para que responda preguntas usando esa información en vez de inventar
respuestas.

**Criterios de aceptación**:
1. Al subir un archivo, el sistema lo fragmenta y lo indexa (embeddings locales).
2. Al preguntar algo relacionado, la respuesta refleja el contenido del
   documento y la traza muestra los fragmentos recuperados con su similitud.
3. Si no hay información relevante, el agente lo indica en vez de inventar.

### US-4 — Orquestar varios agentes en un flujo (Prioridad: P2)
Como Desarrollador, quiero encadenar un agente "Analista" con un agente
"Redactor" para que uno complete el trabajo del otro, demostrando colaboración
multi-agente.

**Criterios de aceptación**:
1. Puedo elegir 2 o más agentes y un texto de entrada inicial.
2. Al ejecutar, veo la salida de cada paso antes de pasar al siguiente.
3. El resultado final es el de el último agente del pipeline.

### US-5 — Monitorear consumo y actividad (Prioridad: P2)
Como Administrador, quiero ver cuántas solicitudes, tokens y qué latencia
generó cada agente, y comparar el costo de modelos locales contra una
referencia de mercado en la nube, para justificar la inversión.

**Criterios de aceptación**:
1. El panel muestra solicitudes, tokens y latencia promedio, global y por
   agente, con datos reales de uso (no de ejemplo estático).
2. El panel muestra el costo local ($0 marginal) frente a un costo de
   referencia estimado si se usara una API comercial equivalente.

### US-6 — Controlar accesos por rol (RBAC) (Prioridad: P3)
Como Administrador, quiero que solo ciertos roles puedan crear, editar o
eliminar agentes, para evitar cambios no autorizados.

**Criterios de aceptación**:
1. Un usuario "solo lectura" puede chatear pero no ve acciones de edición.
2. Un usuario "desarrollador" puede crear/editar pero no eliminar agentes.
3. Un usuario "administrador" tiene acceso completo.

## Fuera de Alcance (explícito)

- Autenticación real / integración con SSO o Active Directory corporativo.
- Múltiples organizaciones/tenants o facturación real.
- Modelos en la nube (OpenAI/Anthropic/etc.) — queda como extensión futura ya
  prevista en la arquitectura (Principio II de la constitución).
- Vectorstore dedicado (Pinecone/Chroma/etc.) a escala de producción.
- Streaming token-a-token de las respuestas (se prioriza fiabilidad de demo).

## Métricas de Éxito del POC

- Un desarrollador puede crear un agente funcional en menos de 2 minutos durante
  la demo, sin tocar código.
- La Gerencia Regional puede, sin ayuda técnica, identificar las 4 capacidades
  clave y su beneficio de negocio solo con la pantalla de "Resumen".
- El costo marginal por interacción demostrado es $0 (modelos 100% locales).
