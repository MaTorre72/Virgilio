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

Push-Location $Root
try {
    $env:PYTHONPATH = Join-Path $Root "local_connector\src"
    $TestRoot = Join-Path $Root (".pytest-tmp-smoke-" + [guid]::NewGuid().ToString("N"))
    & $Python -m pytest -q -p no:cacheprovider --basetemp $TestRoot local_connector
    if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
    & $Python -m virgilio_connector --help | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "CLI help failed" }
    & $Python -m virgilio_connector pilot --help | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Pilot help failed" }

    $tracked = @(git ls-files)
    $forbidden = $tracked | Where-Object {
        $_ -match '(^|/)(\.local_data|\.secrets|_staging)(/|$)' -or
        ($_ -match '(^|/)\.env($|\.)' -and $_ -notmatch '\.env\.example$') -or
        $_ -match '(token|client[_-]?secret|service[_-]?account).*\.json$'
    }
    if ($forbidden) { throw "Tracked secret/local files: $($forbidden -join ', ')" }

    $required = @(
        "AGENTS.md",
        "docs\README.md",
        "docs\sviluppo\CODEX_STATE.md",
        "docs\sviluppo\NEXT_CODEX_TASKS.md",
        "docs\sviluppo\DEV_BACKLOG.md",
        "docs\sviluppo\DEFINITION_OF_DONE.md",
        "docs\tecnica\ARCHITETTURA.md",
        "docs\tecnica\INSTALLAZIONE_E_COMANDI.md"
    )
    foreach ($item in $required) {
        if (-not (Test-Path -LiteralPath (Join-Path $Root $item))) { throw "Missing $item" }
    }
    Write-Host "smoke_local_connector: OK"
}
finally { Pop-Location }
