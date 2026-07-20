param(
    [string]$OutputRoot = "",
    [string]$PythonPath = "",
    [string]$GoogleOAuthClientPath = "",
    [switch]$HumanAcceptanceBuild
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConnectorRoot = Join-Path $RepoRoot "local_connector"
$Python = if ($PythonPath) { [IO.Path]::GetFullPath($PythonPath) } else { Join-Path $ConnectorRoot ".venv\Scripts\python.exe" }
$Spec = Join-Path $ConnectorRoot "build\Caronte.spec"
if (-not $OutputRoot) { $OutputRoot = Join-Path $ConnectorRoot "build-output" }
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$DistPath = Join-Path $OutputRoot "dist"
$WorkPath = Join-Path $OutputRoot "work"
$MetadataPath = Join-Path $OutputRoot "metadata"
$ManifestPath = Join-Path $MetadataPath "build_manifest.json"

if (-not (Test-Path -LiteralPath $Python)) { throw "Runtime di build non trovato. Preparare prima l'ambiente locale del connettore." }
& $Python -c "import tkinter; interpreter=tkinter.Tcl(); interpreter.eval('info patchlevel')"
if ($LASTEXITCODE -ne 0) { throw "Il runtime di build non include Tcl/Tk. Usare una distribuzione Python Windows completa." }

$Commit = (& git -C $RepoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or -not $Commit) { throw "Commit Git non disponibile." }
$ShortCommit = (& git -C $RepoRoot rev-parse --short=7 HEAD).Trim()
$Branch = (& git -C $RepoRoot branch --show-current).Trim()
$StatusLines = @(& git -C $RepoRoot status --porcelain --untracked-files=normal)
$TreeState = if ($StatusLines.Count -gt 0) { "dirty" } else { "clean" }
if ($HumanAcceptanceBuild) {
    if ($TreeState -ne "clean") { throw "Build di collaudo rifiutata: working tree non pulito." }
    if ($Branch -ne "codex/v1.1-development") { throw "Build di collaudo rifiutata: branch sorgente non autorizzata." }
}

$ProjectText = Get-Content -Raw -LiteralPath (Join-Path $ConnectorRoot "pyproject.toml")
$VersionMatch = [regex]::Match($ProjectText, '(?m)^version\s*=\s*"([^"]+)"')
if (-not $VersionMatch.Success) { throw "Versione prodotto non disponibile." }
$Version = $VersionMatch.Groups[1].Value
$PythonVersion = (& $Python -c "import platform; print(platform.python_version())").Trim()
$PyInstallerVersion = (& $Python -c "import PyInstaller; print(PyInstaller.__version__)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $PyInstallerVersion) { throw "Versione PyInstaller non disponibile." }

foreach ($Target in @($DistPath, $WorkPath, $MetadataPath)) {
    if (Test-Path -LiteralPath $Target) { Remove-Item -LiteralPath $Target -Recurse -Force }
}
New-Item -ItemType Directory -Path $MetadataPath -Force | Out-Null
$Manifest = [ordered]@{
    product_name = "Caronte"
    version = $Version
    git_commit = $Commit
    git_short_commit = $ShortCommit
    build_utc = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    source_branch = $Branch
    working_tree = $TreeState
    python_version = $PythonVersion
    pyinstaller_version = $PyInstallerVersion
    build_id = [guid]::NewGuid().ToString()
}
$ManifestJson = $Manifest | ConvertTo-Json
[IO.File]::WriteAllText($ManifestPath, $ManifestJson, (New-Object Text.UTF8Encoding($false)))

$PreviousEpoch = $env:SOURCE_DATE_EPOCH
$PreviousHashSeed = $env:PYTHONHASHSEED
$PreviousGoogleOAuthClientPath = $env:CARONTE_GOOGLE_OAUTH_CLIENT_PATH
$PreviousManifestPath = $env:CARONTE_BUILD_MANIFEST_PATH
try {
    $env:SOURCE_DATE_EPOCH = "1704067200"
    $env:PYTHONHASHSEED = "1"
    $env:CARONTE_BUILD_MANIFEST_PATH = $ManifestPath
    if ($GoogleOAuthClientPath) {
        $GoogleOAuthClientPath = [IO.Path]::GetFullPath($GoogleOAuthClientPath)
        if (-not (Test-Path -LiteralPath $GoogleOAuthClientPath -PathType Leaf)) { throw "Configurazione Google OAuth non trovata." }
        if ([IO.Path]::GetFileName($GoogleOAuthClientPath) -ne "google_oauth_client.json") { throw "Rinominare la configurazione in google_oauth_client.json." }
        & $Python -c "import json,sys; p=json.load(open(sys.argv[1], encoding='utf-8')); assert isinstance(p.get('installed'), dict)" $GoogleOAuthClientPath
        if ($LASTEXITCODE -ne 0) { throw "La configurazione Google non e' un client OAuth Desktop valido." }
        $env:CARONTE_GOOGLE_OAUTH_CLIENT_PATH = $GoogleOAuthClientPath
    } else {
        Remove-Item Env:CARONTE_GOOGLE_OAUTH_CLIENT_PATH -ErrorAction SilentlyContinue
    }
    & $Python -m PyInstaller --clean --noconfirm --distpath $DistPath --workpath $WorkPath $Spec
    if ($LASTEXITCODE -ne 0) { throw "Build Caronte non riuscita." }
}
finally {
    $env:SOURCE_DATE_EPOCH = $PreviousEpoch
    $env:PYTHONHASHSEED = $PreviousHashSeed
    $env:CARONTE_GOOGLE_OAUTH_CLIENT_PATH = $PreviousGoogleOAuthClientPath
    $env:CARONTE_BUILD_MANIFEST_PATH = $PreviousManifestPath
}

$Executable = Join-Path $DistPath "Caronte\Caronte.exe"
$PackagedManifest = Join-Path $DistPath "Caronte\_internal\resources\build_manifest.json"
if (-not (Test-Path -LiteralPath $Executable)) { throw "La build non contiene Caronte.exe." }
if (-not (Test-Path -LiteralPath $PackagedManifest)) { throw "La build non contiene il manifest applicativo." }
Write-Output (Resolve-Path -LiteralPath (Split-Path $Executable -Parent)).Path
