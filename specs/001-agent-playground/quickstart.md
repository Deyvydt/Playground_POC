# Quickstart — TCS Agent Playground

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
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Al iniciar por primera vez, el backend crea `data/playground.db`, siembra 3
usuarios de demostración, 4 agentes de ejemplo, y (si Ollama está disponible)
carga un manual de bienvenida de ejemplo en el agente "Asesor de Onboarding".

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

1. **Resumen** (`/`) — explicar el porqué del proyecto y los 4 beneficios clave.
2. **Agentes** (`/agentes`) — mostrar los agentes ya creados; crear uno nuevo en
   vivo (ej. "Asistente de RRHH") para demostrar lo simple que es configurar uno.
3. Entrar al agente **"Soporte TI"** → pestaña **Playground** → preguntar por el
   estado del ticket `TCS-4471` → expandir la traza para mostrar la llamada a la
   herramienta `consultar_ticket_interno`.
4. Entrar al agente **"Asesor de Onboarding"** → preguntar "¿cuántos días de
   vacaciones acumulo por mes?" → mostrar en la traza el fragmento recuperado del
   manual de bienvenida (RAG).
5. **Flujo Multi-Agente** (`/flujo`) — ejecutar el pipeline
   "Analista de Datos → Redactor de Reportes" con el escenario precargado.
6. **Panel** (`/panel`) — mostrar solicitudes, tokens, latencia y el contraste
   de costo local ($0) vs. una API comercial de referencia.
7. **Configuración** (`/configuracion`) — cambiar de usuario simulado a "Lucía
   Soto" (solo lectura) y mostrar cómo desaparecen las acciones de edición.

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| Badge "Ollama desconectado" | El servicio Ollama no está corriendo | Ejecutar `ollama serve` (o abrir la app de Ollama) |
| Subir un documento falla | Falta el modelo de embeddings | `ollama pull nomic-embed-text` |
| Respuestas muy lentas | Modelo pesado en CPU | Usar `llama3.2:3b` en el agente durante la demo |
