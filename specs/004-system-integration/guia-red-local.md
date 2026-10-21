# Guía: conectar el sistema de otro equipo a TokenIO por la red local

Para quien lo hace por primera vez. Lee primero los conceptos; después sigue los
pasos en orden. Los casos de prueba que usan esta guía están en
`plan-de-pruebas.md` (fase C).

## 1. La idea en una frase

Hoy el agente del otro equipo llama **directo** al proveedor (o a su propio Ollama)
con una API key real. Después llamará a **TokenIO**, que está en tu PC, con una
**virtual key** que tú le das. TokenIO reenvía la llamada al modelo, anota los
tokens y el costo, y puede bloquearla.

```
ANTES:  agente del otro equipo ──(API key real)──────────────► proveedor / Ollama

AHORA:  agente del otro equipo ──(virtual key)──► TokenIO (tu PC) ──► proveedor / Ollama
                                                  │
                                                  ├─ anota tokens, costo, latencia
                                                  ├─ aplica presupuesto y límites
                                                  └─ si lo pausas: responde 401
```

Por eso **sí** necesitan estar los dos sistemas levantados y en la **misma red**:
el agente de la PC 2 tiene que poder llegar a tu PC por la red.

## 2. Conceptos (en español)

| Término | Qué significa | Para qué sirve aquí |
|---|---|---|
| **Red local / LAN** (*Local Area Network*, red de área local) | Las computadoras conectadas al mismo router o Wi-Fi. | Las dos PCs se ven entre sí sin pasar por internet. |
| **IP** (*Internet Protocol*) | La "dirección" de una PC en la red, p. ej. `192.168.1.50`. | El otro equipo la usa para encontrar tu PC. |
| **Puerto** | Un "número de puerta" dentro de la PC; cada servicio escucha en uno. | El gateway escucha en el **4000**. |
| **localhost / 127.0.0.1** | "Esta misma PC". Un servicio que escucha ahí **solo** acepta conexiones de la misma PC. | Así están hoy todos los servicios: invisibles para la red. |
| **0.0.0.0** | "Todas las interfaces de red": acepta conexiones de otras PCs. | Se lo pones **solo al gateway** para que lo vean. |
| **Firewall** (cortafuegos) | El portero de Windows: bloquea conexiones entrantes que no autorizaste. | Hay que abrirle el puerto 4000. |
| **DHCP** (*Dynamic Host Configuration Protocol*) | El router reparte IPs automáticamente; a veces te cambia la IP. | Si cambia, hay que actualizar la URL que tienen ellos. |
| **Virtual key** | Una key falsa que emite TokenIO (`sk-...`); no sirve fuera de TokenIO. | Identifica al agente, lleva su presupuesto y se puede bloquear. |
| **Base URL** | La dirección a la que el SDK manda las llamadas al modelo. | Es lo principal que cambia en el sistema del otro equipo. |
| **Alias de modelo** | Nombre lógico del modelo en TokenIO (`llama-local`, `claude-sonnet`). | Ellos piden el alias; TokenIO decide qué modelo real usa. |

## 3. Qué cambia en cada sistema

**En TokenIO (tu PC)** no cambia código, solo configuración:
1. El gateway escucha en `0.0.0.0` en vez de `127.0.0.1`.
2. Governance anuncia tu IP en la guía de conexión (`GATEWAY_PUBLIC_URL`).
3. Registras su agente en **Gobierno → Registrar agente** y copias la key.

**En el sistema del otro equipo** cambian tres valores y, idealmente, el manejo de
errores:

| Antes | Después |
|---|---|
| URL del proveedor (`https://api.openai.com/v1`, `https://api.anthropic.com`) o su Ollama | `http://<tu-ip>:4000/v1` (formato OpenAI) o `http://<tu-ip>:4000/anthropic` (SDK de Anthropic) |
| API key real del proveedor | La virtual key que les das |
| Nombre real del modelo (`gpt-4o`, `claude-…`, `llama3.2`) | El alias: `llama-local` (o `claude-sonnet` en la fase C2) |
| Errores del proveedor | Mostrar un mensaje claro ante 401, 403, 422 y 429 (sección 7) |

Para saber exactamente dónde cambiarlo, busca en su repositorio (o pásame el
nombre del repositorio y lo reviso):

```bash
git grep -n -i -E "api_key|base_url|api.openai.com|api.anthropic.com|ChatOpenAI|ChatAnthropic|OpenAI\(|Anthropic\(|langchain4j|11434|OLLAMA"
```

Lo ideal es que esos tres valores vengan de variables de entorno (`.env`), así
pueden volver al proveedor directo sin tocar código.

## 4. Paso a paso en tu PC (TokenIO, el "servidor")

1. **Misma red.** Conecta ambas PCs al mismo router o Wi-Fi. En Windows:
   Configuración → Red e Internet → tu red → **Perfil de red: Privada** (en
   "Pública" Windows bloquea las conexiones entrantes).
2. **Tu IP.** En PowerShell: `ipconfig` y busca "Dirección IPv4" del adaptador que
   usas (Wi-Fi o Ethernet), p. ej. `192.168.1.50`. Ignora las que empiezan por
   `127.` o `169.254.`.
3. **Gateway visible.** En `services/gateway/.env`: `GATEWAY_HOST=0.0.0.0`.
4. **URL que verán ellos.** En `services/governance/.env`:
   `GATEWAY_PUBLIC_URL=http://192.168.1.50:4000` (tu IP).
5. **Firewall.** PowerShell **como administrador**:
   ```powershell
   New-NetFirewallRule -DisplayName "TokenIO gateway" -Direction Inbound -Protocol TCP -LocalPort 4000 -Action Allow -Profile Private
   ```
6. **Levanta todo:** `.\scripts\dev-up.ps1` (gateway, governance, backend,
   agent-lab y frontend en orden).
7. **Prueba desde tu propia PC usando la IP** (no `localhost`):
   ```powershell
   curl.exe http://192.168.1.50:4000/health/liveliness
   ```
   Debe responder `"I'm alive!"`. Si responde con `localhost` pero no con la IP,
   revisa el paso 3.
8. **Registra su agente:** TokenIO → **Gobierno** → **Sistema** (crea uno para su
   proyecto, en el área que corresponda) → **Registrar agente**: nombre, sistema,
   encargado y correo, modelos (`Modelos locales`), presupuesto y periodo, límites.
9. **Copia la key** (se muestra **una sola vez**) y la guía de conexión (Python,
   Java o cURL ya traen tu IP). Pásasela al otro equipo por un canal privado
   (nunca en un repositorio ni en un chat grupal).

## 5. Paso a paso en la PC del otro equipo (el "cliente")

1. **¿Llega a tu PC?**
   ```powershell
   Test-NetConnection 192.168.1.50 -Port 4000
   ```
   Debe decir `TcpTestSucceeded : True`.
2. **¿La key funciona?**
   ```powershell
   curl.exe http://192.168.1.50:4000/v1/models -H "Authorization: Bearer sk-SU-VIRTUAL-KEY"
   ```
   Debe listar `llama-local` (y `embed-local`).
3. **Cambia la configuración de su agente** (ejemplos):

   *Python con LangChain*
   ```python
   from langchain_openai import ChatOpenAI
   llm = ChatOpenAI(base_url="http://192.168.1.50:4000/v1", api_key=os.environ["TOKENIO_KEY"], model="llama-local")
   ```
   *Python con el SDK de OpenAI*
   ```python
   from openai import OpenAI
   client = OpenAI(base_url="http://192.168.1.50:4000/v1", api_key=os.environ["TOKENIO_KEY"])
   client.chat.completions.create(model="llama-local", messages=[{"role": "user", "content": "Hola"}])
   ```
   *Python con el SDK de Anthropic* (fase C2, modelo en la nube)
   ```python
   from anthropic import Anthropic
   client = Anthropic(base_url="http://192.168.1.50:4000/anthropic", api_key=os.environ["TOKENIO_KEY"])
   client.messages.create(model="claude-sonnet", max_tokens=200, messages=[{"role": "user", "content": "Hola"}])
   ```
   *Java con Quarkus + LangChain4j* (`application.properties`)
   ```properties
   quarkus.langchain4j.openai.base-url=http://192.168.1.50:4000/v1
   quarkus.langchain4j.openai.api-key=${TOKENIO_KEY}
   quarkus.langchain4j.openai.chat-model.model-name=llama-local
   quarkus.langchain4j.openai.timeout=120s
   ```
4. **Opcional, para ver sus ejecuciones agrupadas en Langfuse:** enviar en cada
   llamada `metadata: {"trace_id": "<id de su ejecución>", "generation_name": "<paso>"}`
   (en LangChain: `llm.invoke(..., extra_body={"metadata": {...}})`).
5. Ejecutan su flujo normal.

## 6. Qué vas a ver en TokenIO

| Dónde | Qué |
|---|---|
| **Gobierno** → tarjeta del área | Gasto del área frente a su presupuesto |
| **Gobierno** → fila del agente | Estado, gasto del periodo, "Última actividad hace X" |
| **Gobierno** → clic en el agente | Actividad de las últimas 24 h: cada llamada con modelo, estado, tokens, latencia y costo |
| **Campana** | Avisos: 80 % del presupuesto, pausas manuales y automáticas |
| **Langfuse** (si está activo) | Trazas por ejecución, con tags `agent:`, `area:`, `sistema:` |

El gasto se actualiza en la base del gateway cada ~60 s; el control de presupuesto
es inmediato.

## 7. Cómo los bloqueas y qué les sale a ellos

**Gobierno → botón Pausar** (pide motivo). La key queda bloqueada al instante en
el gateway. Su siguiente llamada recibe:

| Código | Cuándo | Qué debería mostrar su sistema |
|---|---|---|
| **401** | Agente pausado, key regenerada o dada de baja, key mal copiada | "El servicio de IA está pausado por el administrador" |
| **403** | Pidió un modelo que su key no tiene | "Modelo no habilitado" |
| **422** | Se acabó el presupuesto del periodo | "Presupuesto agotado" |
| **429** | Superó el límite de solicitudes o tokens por minuto | "Demasiadas solicitudes, intenta en un minuto" |

**Reactivar** lo desbloquea sin que ellos cambien nada. **Regenerar key** invalida
la anterior: tendrás que pasarles la nueva.

## 8. Comandos útiles para las pruebas

Llamada directa con la key de un agente (útil para la fase A y para ellos):

```powershell
curl.exe http://192.168.1.50:4000/v1/chat/completions `
  -H "Authorization: Bearer sk-SU-VIRTUAL-KEY" -H "Content-Type: application/json" `
  -d '{\"model\": \"llama-local\", \"messages\": [{\"role\": \"user\", \"content\": \"Hola\"}]}'
```

Provocar errores a propósito (caso A-23, auto-pausa por tasa de errores): repetir
5 veces cambiando el cuerpo a
`{\"model\": \"llama-local\", \"temperature\": \"abc\", \"messages\": [{\"role\": \"user\", \"content\": \"x\"}]}`.

## 9. Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `TcpTestSucceeded : False` | Firewall, red "Pública", gateway en 127.0.0.1 | Pasos 1, 3 y 5 de la sección 4 |
| Funciona en tu PC con la IP pero no desde la otra | Wi-Fi de invitados o corporativo con aislamiento de clientes | Usar otro router, un hotspot propio o cable |
| Dejó de funcionar al día siguiente | Cambió tu IP (DHCP) | `ipconfig`, actualizar `GATEWAY_PUBLIC_URL` y avisarles la nueva URL (la key sigue sirviendo) |
| 401 desde el principio | Key mal copiada (espacios, incompleta) o agente pausado | Revisar en Gobierno; regenerar si hace falta |
| Timeout en la primera llamada | Ollama cargando el modelo | Hacer una llamada previa en tu PC; timeout del cliente ≥ 120 s |
| 404 en `/anthropic/...` | Versión de LiteLLM con otra ruta | Probar `base_url` sin `/anthropic` (ver documentación de LiteLLM) |

## 10. Seguridad

- La **master key** del gateway y las API keys reales nunca salen de tu PC.
- Cada agente del otro equipo tiene **su propia** virtual key: así se atribuye el
  gasto y se puede pausar uno sin afectar a los demás.
- Las keys van en `.env` (ignorado por git), nunca en el código ni en capturas.
- Al terminar las pruebas: vuelve `GATEWAY_HOST=127.0.0.1` y desactiva la regla
  del firewall (`Disable-NetFirewallRule -DisplayName "TokenIO gateway"`).
