param(
    [string]$Python = "python",
    [string]$VenvPath
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConnectorRoot = Join-Path $Root "local_connector"
if (-not $VenvPath) { $VenvPath = Join-Path $ConnectorRoot ".venv" }
$VenvPath = [IO.Path]::GetFullPath($VenvPath)
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

& $Python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 o successivo richiesto." }

if (-not (Test-Path -LiteralPath $VenvPython)) {
    & $Python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) { throw "Creazione ambiente virtuale non riuscita." }
}

# Runtime e tooling di test provengono dalla sola dichiarazione autorevole.
& $VenvPython -m pip install -e "$ConnectorRoot[dev]"
if ($LASTEXITCODE -ne 0) { throw "Installazione dipendenze di sviluppo non riuscita." }

& $VenvPython -m virgilio_connector --help | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Verifica CLI non riuscita." }
Write-Output "bootstrap_local_connector: OK ($VenvPython)"
