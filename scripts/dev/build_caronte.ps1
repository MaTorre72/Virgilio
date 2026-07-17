param(
    [string]$OutputRoot = "",
    [string]$PythonPath = "",
    [string]$GoogleOAuthClientPath = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConnectorRoot = Join-Path $RepoRoot "local_connector"
$Python = if ($PythonPath) {
    [IO.Path]::GetFullPath($PythonPath)
} else {
    Join-Path $ConnectorRoot ".venv\Scripts\python.exe"
}
$Spec = Join-Path $ConnectorRoot "build\Caronte.spec"

if (-not $OutputRoot) {
    $OutputRoot = Join-Path $ConnectorRoot "build-output"
}
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$DistPath = Join-Path $OutputRoot "dist"
$WorkPath = Join-Path $OutputRoot "work"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Runtime di build non trovato. Preparare prima l'ambiente locale del connettore."
}
& $Python -c "import tkinter; interpreter=tkinter.Tcl(); interpreter.eval('info patchlevel')"
if ($LASTEXITCODE -ne 0) {
    throw "Il runtime di build non include Tcl/Tk. Usare una distribuzione Python Windows completa."
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$PreviousEpoch = $env:SOURCE_DATE_EPOCH
$PreviousHashSeed = $env:PYTHONHASHSEED
$PreviousGoogleOAuthClientPath = $env:CARONTE_GOOGLE_OAUTH_CLIENT_PATH
try {
    $env:SOURCE_DATE_EPOCH = "1704067200"
    $env:PYTHONHASHSEED = "1"
    if ($GoogleOAuthClientPath) {
        $GoogleOAuthClientPath = [IO.Path]::GetFullPath($GoogleOAuthClientPath)
        if (-not (Test-Path -LiteralPath $GoogleOAuthClientPath -PathType Leaf)) {
            throw "Configurazione Google OAuth non trovata."
        }
        if ([IO.Path]::GetFileName($GoogleOAuthClientPath) -ne "google_oauth_client.json") {
            throw "Rinominare la configurazione in google_oauth_client.json."
        }
        & $Python -c "import json,sys; p=json.load(open(sys.argv[1], encoding='utf-8')); assert isinstance(p.get('installed'), dict)" $GoogleOAuthClientPath
        if ($LASTEXITCODE -ne 0) { throw "La configurazione Google non e' un client OAuth Desktop valido." }
        $env:CARONTE_GOOGLE_OAUTH_CLIENT_PATH = $GoogleOAuthClientPath
    } else {
        Remove-Item Env:CARONTE_GOOGLE_OAUTH_CLIENT_PATH -ErrorAction SilentlyContinue
    }
    & $Python -m PyInstaller --clean --noconfirm --distpath $DistPath --workpath $WorkPath $Spec
    if ($LASTEXITCODE -ne 0) {
        throw "Build Caronte non riuscita."
    }
}
finally {
    $env:SOURCE_DATE_EPOCH = $PreviousEpoch
    $env:PYTHONHASHSEED = $PreviousHashSeed
    $env:CARONTE_GOOGLE_OAUTH_CLIENT_PATH = $PreviousGoogleOAuthClientPath
}

$Executable = Join-Path $DistPath "Caronte\Caronte.exe"
if (-not (Test-Path -LiteralPath $Executable)) {
    throw "La build non contiene Caronte.exe."
}
Write-Output (Resolve-Path -LiteralPath (Split-Path $Executable -Parent)).Path
