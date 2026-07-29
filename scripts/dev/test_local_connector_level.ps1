param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("unit", "contract", "integration_offline")]
    [string]$Level
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RootVenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$PackageVenvPython = Join-Path $Root "local_connector\.venv\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $RootVenvPython) {
    $RootVenvPython
} elseif (Test-Path -LiteralPath $PackageVenvPython) {
    $PackageVenvPython
} else {
    "python"
}
$TestRoot = Join-Path $Root (".pytest-tmp-" + $Level + "-" + [guid]::NewGuid().ToString("N"))

Push-Location $Root
try {
    $env:PYTHONPATH = Join-Path $Root "local_connector\src"
    & $Python -m pytest -q -p no:cacheprovider --basetemp $TestRoot -m $Level local_connector
    if ($LASTEXITCODE -ne 0) { throw "$Level tests failed" }
}
finally { Pop-Location }
