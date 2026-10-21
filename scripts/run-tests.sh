#!/usr/bin/env bash
# Ejecuta todas las pruebas de TokenIO (Linux, macOS, CI). Crea .venv-tests/ la primera vez
# y reinstala dependencias solo si cambió algún requirements.txt.
# Uso: scripts/run-tests.sh [--tipo funcional|tecnica] [--componente X] [--rapido]
set -euo pipefail
cd "$(dirname "$0")/.."

VENV=.venv-tests
PY="$VENV/bin/python"
REQS="tests/requirements.txt backend/requirements.txt services/governance/requirements.txt services/agent-lab/requirements.txt"

if [ ! -x "$PY" ]; then
  echo "Creando entorno de pruebas en $VENV..."
  python3 -m venv "$VENV"
fi
HASH=$(cat $REQS | "$PY" -c "import hashlib,sys;print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())")
if [ "$(cat "$VENV/.reqs-hash" 2>/dev/null)" != "$HASH" ]; then
  echo "Instalando dependencias de prueba..."
  "$PY" -m pip install -q --upgrade pip
  "$PY" -m pip install -q -r tests/requirements.txt
  echo "$HASH" > "$VENV/.reqs-hash"
fi

exec "$PY" scripts/run-tests.py "$@"
