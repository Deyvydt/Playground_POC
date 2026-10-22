<#
.SYNOPSIS
  Levanta TokenIO completo en Windows, en orden: Postgres + gateway, governance,
  backend, agent-lab y frontend. Cada servicio abre su propia ventana de PowerShell.

.DESCRIPTION
  Requiere los entornos virtuales (.venv) y los .env ya creados (ver services/README.md).
  El orden importa: governance necesita el gateway; el backend registra sus agentes en
  governance al arrancar; agent-lab y governance validan sesiones contra el backend.

.PARAMETER Lan
  Expone el frontend en la red local (npm run dev -- --host). Para exponer el gateway,
  poner GATEWAY_HOST=0.0.0.0 en services/gateway/.env.

.PARAMETER SinLab
  No levanta agent-lab.

.EXAMPLE
  .\scripts\dev-up.ps1
  .\scripts\dev-up.ps1 -Lan
#>
param(
  [switch]$Lan,
  [switch]$SinLab
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Assert-Path($Path, $Hint) {
  if (-not (Test-Path $Path)) {
    Write-Host "Falta $Path" -ForegroundColor Red
    Write-Host "  $Hint" -ForegroundColor Yellow
    exit 1
  }
}

function Start-TokenIOService($Title, $Dir, $Command) {
  Write-Host "-> $Title" -ForegroundColor Cyan
  $script = "`$Host.UI.RawUI.WindowTitle = 'TokenIO · $Title'; Set-Location '$Dir'; $Command"
  Start-Process powershell -ArgumentList "-NoExit", "-Command", $script | Out-Null
}

function Wait-Url($Name, $Url, $TimeoutSeconds = 180) {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    try {
      $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
      if ($r.StatusCode -eq 200) {
        Write-Host "   $Name en línea" -ForegroundColor Green
        return
      }
    } catch { }
    Start-Sleep -Seconds 2
  }
  Write-Host "   $Name no respondió en $TimeoutSeconds s ($Url). Revisa su ventana." -ForegroundColor Red
  exit 1
}

$gateway = Join-Path $Root "services\gateway"
$governance = Join-Path $Root "services\governance"
$agentLab = Join-Path $Root "services\agent-lab"
$backend = Join-Path $Root "backend"
$frontend = Join-Path $Root "frontend"

Assert-Path "$gateway\.venv" "cd services\gateway; python -m venv .venv; .venv\Scripts\python -m pip install -r requirements.txt"
Assert-Path "$gateway\.env" "Copia services\gateway\.env.example a .env y completa las claves"
Assert-Path "$governance\.venv" "cd services\governance; python -m venv .venv; .venv\Scripts\python -m pip install -r requirements.txt"
Assert-Path "$governance\.env" "Copia services\governance\.env.example a .env y completa las claves"
Assert-Path "$backend\.venv" "cd backend; python -m venv .venv; .venv\Scripts\python -m pip install -r requirements.txt"
Assert-Path "$frontend\node_modules" "cd frontend; npm install"
if (-not $SinLab) {
  Assert-Path "$agentLab\.venv" "cd services\agent-lab; python -m venv .venv; .venv\Scripts\python -m pip install -r requirements.txt"
  Assert-Path "$agentLab\.env" "Copia services\agent-lab\.env.example a .env y completa las claves"
}

Write-Host "Levantando TokenIO..." -ForegroundColor White

# start.py arranca Postgres (:5433) y luego el gateway (:4000).
Start-TokenIOService "Gateway" $gateway ".venv\Scripts\python start.py"
Wait-Url "Gateway" "http://127.0.0.1:4000/health/liveliness" 300

# Las áreas (teams) deben existir antes de que el backend siembre el conocimiento vía gateway.
# bootstrap.py es idempotente.
Write-Host "-> Áreas del gateway" -ForegroundColor Cyan
& "$gateway\.venv\Scripts\python.exe" "$gateway\bootstrap.py"
if ($LASTEXITCODE -ne 0) { Write-Host "   bootstrap.py falló" -ForegroundColor Red; exit 1 }

Start-TokenIOService "Governance" $governance ".venv\Scripts\python -m uvicorn app.main:app --port 8100"
Wait-Url "Governance" "http://127.0.0.1:8100/gov/health"

Start-TokenIOService "Backend" $backend ".venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"
Wait-Url "Backend" "http://127.0.0.1:8000/api/health"

if (-not $SinLab) {
  Start-TokenIOService "Agent Lab" $agentLab ".venv\Scripts\python -m uvicorn app.main:app --port 8200"
  Wait-Url "Agent Lab" "http://127.0.0.1:8200/lab/health"
  # Registra los nodos de prueba en governance; idempotente.
  Push-Location $agentLab
  & ".venv\Scripts\python.exe" "provision.py"
  $provisionExit = $LASTEXITCODE
  Pop-Location
  if ($provisionExit -ne 0) { Write-Host "   provision.py falló" -ForegroundColor Red; exit 1 }
}

$viteArgs = if ($Lan) { "npm run dev -- --host" } else { "npm run dev" }
Start-TokenIOService "Frontend" $frontend $viteArgs
Wait-Url "Frontend" "http://localhost:5173" 120

Write-Host ""
Write-Host "Listo: http://localhost:5173" -ForegroundColor Green
if ($Lan) {
  $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } | Select-Object -First 1).IPAddress
  Write-Host "En la red local: http://${ip}:5173 · gateway: http://${ip}:4000/v1" -ForegroundColor Green
}
