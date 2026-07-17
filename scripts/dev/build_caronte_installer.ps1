param(
    [string]$PythonPath = "",
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConnectorRoot = Join-Path $RepoRoot "local_connector"
$Python = if ($PythonPath) { [IO.Path]::GetFullPath($PythonPath) } else { Join-Path $ConnectorRoot ".venv\Scripts\python.exe" }
$Payload = Join-Path $ConnectorRoot "build-output\dist\Caronte\Caronte.exe"
$Spec = Join-Path $ConnectorRoot "installer\CaronteSetup.spec"
if (-not $OutputRoot) { $OutputRoot = Join-Path $ConnectorRoot "build-output\installer" }
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)

if (-not (Test-Path -LiteralPath $Python)) { throw "Runtime di build non trovato." }
if (-not (Test-Path -LiteralPath $Payload)) { throw "Creare prima la build autonoma di Caronte." }
& $Python -c "import tkinter; print(tkinter.Tcl().eval('info patchlevel'))"
if ($LASTEXITCODE -ne 0) { throw "La toolchain non include Tcl/Tk completo." }

$DistPath = Join-Path $OutputRoot "dist"
$WorkPath = Join-Path $OutputRoot "work"
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
& $Python -m PyInstaller --clean --noconfirm --distpath $DistPath --workpath $WorkPath $Spec
if ($LASTEXITCODE -ne 0) { throw "Build dell'installer non riuscita." }
$Installer = Join-Path $DistPath "CaronteSetup.exe"
if (-not (Test-Path -LiteralPath $Installer)) { throw "CaronteSetup.exe non prodotto." }
Write-Output (Resolve-Path -LiteralPath $Installer).Path
