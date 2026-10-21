<#
.SYNOPSIS
  Ejecuta todas las pruebas de TokenIO en Windows y genera el reporte en reports\.

.DESCRIPTION
  Crea .venv-tests\ la primera vez y reinstala dependencias solo si cambió algún
  requirements.txt. Los parámetros se pasan tal cual a scripts\run-tests.py.

.EXAMPLE
  .\scripts\run-tests.ps1
  .\scripts\run-tests.ps1 --tipo funcional
  .\scripts\run-tests.ps1 --componente governance --rapido
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Venv = Join-Path $Root ".venv-tests"
$Py = Join-Path $Venv "Scripts\python.exe"
$Reqs = @("tests\requirements.txt", "backend\requirements.txt", "services\governance\requirements.txt", "services\agent-lab\requirements.txt")

if (-not (Test-Path $Py)) {
  Write-Host "Creando entorno de pruebas en .venv-tests..." -ForegroundColor Cyan
  python -m venv $Venv
  if ($LASTEXITCODE -ne 0) { Write-Host "No se pudo crear el entorno. ¿Está Python en el PATH?" -ForegroundColor Red; exit 2 }
}

$Hash = (Get-FileHash -Algorithm SHA256 -InputStream ([IO.MemoryStream]::new([byte[]]($Reqs | ForEach-Object { [IO.File]::ReadAllBytes((Join-Path $Root $_)) } | ForEach-Object { $_ })))).Hash
$Marker = Join-Path $Venv ".reqs-hash"
if (-not (Test-Path $Marker) -or (Get-Content $Marker) -ne $Hash) {
  Write-Host "Instalando dependencias de prueba..." -ForegroundColor Cyan
  & $Py -m pip install -q --upgrade pip
  & $Py -m pip install -q -r tests\requirements.txt
  if ($LASTEXITCODE -ne 0) { Write-Host "Falló la instalación de dependencias." -ForegroundColor Red; exit 2 }
  Set-Content -Path $Marker -Value $Hash
}

& $Py scripts\run-tests.py @args
$code = $LASTEXITCODE
$Report = Join-Path $Root "reports\reporte.html"
if (-not $env:CI -and (Test-Path $Report)) { Start-Process $Report -ErrorAction SilentlyContinue }
exit $code
