# Quickstart — Agent Playground

## Requisitos previos

- Python 3.11+ y Node.js 18+
- [Ollama](https://ollama.com) instalado y corriendo (`ollama serve` si no inicia solo)
- Modelos locales descargados:
  ```bash
  ollama pull llama3.2:3b
  ollama pull mistral
  ollama pull nomic-embed-text   # requerido para RAG (conocimiento interno)
  ```

## 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Al iniciar por primera vez, el backend crea `data/playground.db`, siembra 3
cuentas, 6 agentes de ejemplo, un historial de uso de 30 días (desactivable con
`SEED_DEMO_ACTIVITY=false`) y, si Ollama está disponible, el manual de
bienvenida en el agente "Asesor de Onboarding". Si ya existía una base de la
versión anterior, se migra automáticamente.

### Cuentas

| Correo | Rol | Contraseña |
|---|---|---|
| `ana.rios@tcs.com` | Administrador | `Tcs2026!` |
| `carlos.vega@tcs.com` | Desarrollador | `Tcs2026!` |
| `lucia.soto@tcs.com` | Usuario | `Tcs2026!` |

Verificar: `http://localhost:8000/api/health` → `{"ollama_available": true}`.
Documentación interactiva: `http://localhost:8000/docs`.

## 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Abrir `http://localhost:5173`. El proxy de Vite reenvía `/api/*` al backend en
el puerto 8000 (ver `vite.config.js`), por lo que ambos deben estar corriendo.

## 3. Guion sugerido para la demo

1. **Login** — entrar como Ana (Administradora). Mostrar el acceso por cuenta.
2. **Inicio** (`/`) — tokens consumidos, costo evitado frente a la nube,
   agentes con mayor consumo y actividad reciente.
3. **Agentes** (`/agentes`) — crear uno en vivo (ej. "Asistente de Compras")
   con ícono, instrucciones, modelo y herramientas.
4. Agente **"Soporte TI"** → sugerencia "¿Cuál es el estado del ticket
   TCS-4471?" → abrir "Ver razonamiento" para mostrar la herramienta invocada.
5. Agente **"Asesor de Onboarding"** → "¿Cuántos días de vacaciones acumulo por
   mes?" → en el razonamiento, el fragmento recuperado del manual.
6. **Flujos** (`/flujos`) — plantilla "Análisis de margen" → ver avanzar cada
   agente en vivo y el resultado final.
7. **Consumo** (`/consumo`) — tokens de entrada/salida por agente, usuario y
   modelo; cambiar el periodo a 7/30/90 días.
8. **Usuarios** (`/usuarios`) — crear una cuenta; luego cerrar sesión y entrar
   como Lucía (Usuario) para mostrar que no ve Consumo, Usuarios ni acciones de
   edición.

Atajos: `Ctrl+K` buscador global, `Ctrl+B` plegar el menú lateral.

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| Indicador "Motor de modelos sin conexión" | El servicio Ollama no está corriendo | Ejecutar `ollama serve` (o abrir la app de Ollama) |
| Subir un documento falla | Falta el modelo de embeddings | `ollama pull nomic-embed-text` |
| Respuestas muy lentas | Modelo pesado en CPU | Usar `llama3.2:3b` en el agente durante la demo |
