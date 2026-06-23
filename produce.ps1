<#
  Comando rápido MZSHARD — genera un video animado (completo + short) con tu voz.

  EJEMPLOS (abre PowerShell en la carpeta del proyecto):
    .\produce.ps1 "Los 5 errores que arruinan un Data Lake"
    .\produce.ps1 "BigQuery vs Snowflake" -voz f5 -detalles "enfoque en costos"
    .\produce.ps1 "Entrevista Data Architect" -planfile youtube_pipeline\examples\plans\p11_entrevista_data_architect.json -voz f5
    .\produce.ps1 -lote mis_ideas.txt -voz elevenlabs        # varias ideas (una por línea)

  Las entregas quedan en la carpeta  entregas\
#>
param(
  [Parameter(Position = 0)][string]$Tema,
  [ValidateSet("f5", "elevenlabs")][string]$voz = "elevenlabs",
  [string]$detalles = "",
  [string]$planfile = "",
  [string]$lote = "",
  [string]$musica = "",
  [double]$velocidad = 1.0,
  [switch]$noshort
)

$ErrorActionPreference = "Stop"
$py = Join-Path $PSScriptRoot ".venv-voz\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "No existe $py. ¿Creaste el entorno .venv-voz? (ver SETUP_VOZ_LOCAL.md)" }

$env:PYTHONUTF8 = "1"
$env:HF_HUB_DISABLE_XET = "1"

$a = @("-m", "youtube_pipeline.producir")
if ($Tema)     { $a += $Tema }
$a += @("--voz", $voz)
if ($detalles) { $a += @("--detalles", $detalles) }
if ($planfile) { $a += @("--plan-file", $planfile) }
if ($lote)     { $a += @("--lote", $lote) }
if ($musica)   { $a += @("--musica", $musica) }
$a += @("--velocidad", "$velocidad")
if ($noshort)  { $a += "--no-short" }

Write-Host "MZSHARD -> generando ($voz)..." -ForegroundColor Cyan
& $py @a
