---
name: demo-playground
description: Levanta el backend (FastAPI) y el frontend (Vite) del TCS Agent Playground para una demo local, y verifica que Ollama esté disponible con los modelos requeridos. Usar cuando el usuario pida "levantar el playground", "iniciar la demo" o "correr el proyecto".
---

# Levantar TCS Agent Playground para demo

## 1. Verificar prerrequisitos

```bash
ollama list
```

Deben aparecer `llama3.2:3b`, `mistral` (o `mistral:latest`) y `nomic-embed-text`.
Si falta alguno:
```bash
ollama pull llama3.2:3b
ollama pull mistral
ollama pull nomic-embed-text
```

Si `ollama list` falla, iniciar el servicio con `ollama serve` (o abrir la app
de Ollama) antes de continuar.

## 2. Backend (puerto 8000)

Desde la raíz del repo:
```bash
cd backend
python -m venv .venv && .venv/bin/pip install -r requirements.txt   # solo la primera vez
.venv/bin/uvicorn app.main:app --reload --port 8000
```
Ejecutar en segundo plano (background) para no bloquear la terminal. Confirmar
con `curl http://localhost:8000/api/health` que responde
`{"status":"ok","ollama_available":true}`.

## 3. Frontend (puerto 5173)

En otra terminal/proceso en background:
```bash
cd frontend
npm install   # solo si es la primera vez o cambió package.json
npm run dev
```
Confirmar que Vite reporta el servidor en `http://localhost:5173`.

## 4. Verificación rápida antes de la demo

- Abrir `http://localhost:5173` → debe cargar el login con el logo de TCS.
  Entrar con `ana.rios@tcs.com` / `Tcs2026!`.
- El indicador superior derecho debe decir "Motor de modelos en línea".
- Entrar a un agente (ej. "Soporte TI") y enviar un mensaje de prueba en la
  pestaña Playground para confirmar que el modelo responde.

## Notas

- Ambos procesos deben quedar corriendo simultáneamente durante toda la demo.
- Si algo fallara en vivo, el guion completo de fallback está en
  `specs/001-agent-playground/quickstart.md` ("Solución de problemas").
