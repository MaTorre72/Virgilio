param(
    [string]$PythonPath = "",
    [string]$OutputRoot = "",
    [string]$GoogleOAuthClientPath = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConnectorRoot = Join-Path $RepoRoot "local_connector"
$Python = if ($PythonPath) { [IO.Path]::GetFullPath($PythonPath) } else { Join-Path $ConnectorRoot ".venv\Scripts\python.exe" }
$BuildRoot = Join-Path $ConnectorRoot "build-output"
if (-not $OutputRoot) { $OutputRoot = Join-Path $BuildRoot "installer" }
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$DistPath = Join-Path $OutputRoot "dist"
$WorkPath = Join-Path $OutputRoot "work"
$BuildScript = Join-Path $PSScriptRoot "build_caronte.ps1"
$BuildArguments = @{ OutputRoot = $BuildRoot; PythonPath = $Python; HumanAcceptanceBuild = $true }
if ($GoogleOAuthClientPath) { $BuildArguments.GoogleOAuthClientPath = $GoogleOAuthClientPath }

& $BuildScript @BuildArguments | Out-Null
$Payload = Join-Path $BuildRoot "dist\Caronte"
$BuildManifestPath = Join-Path $BuildRoot "metadata\build_manifest.json"
$BuildManifest = Get-Content -Raw -LiteralPath $BuildManifestPath | ConvertFrom-Json
$InstallerBaseName = "CaronteSetup-$($BuildManifest.version)-$($BuildManifest.git_short_commit)"
$Spec = Join-Path $ConnectorRoot "installer\CaronteSetup.spec"

foreach ($Target in @($DistPath, $WorkPath)) {
    if (Test-Path -LiteralPath $Target) { Remove-Item -LiteralPath $Target -Recurse -Force }
}
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
& (Join-Path $PSScriptRoot "smoke_caronte_build.ps1") -BuildDirectory $Payload -ExpectedBuildManifest $BuildManifestPath | Out-Null

$PreviousPayload = $env:CARONTE_PAYLOAD_DIR
$PreviousInstallerName = $env:CARONTE_INSTALLER_BASENAME
try {
    $env:CARONTE_PAYLOAD_DIR = $Payload
    $env:CARONTE_INSTALLER_BASENAME = $InstallerBaseName
    & $Python -m PyInstaller --clean --noconfirm --distpath $DistPath --workpath $WorkPath $Spec
    if ($LASTEXITCODE -ne 0) { throw "Build dell'installer non riuscita." }
}
finally {
    $env:CARONTE_PAYLOAD_DIR = $PreviousPayload
    $env:CARONTE_INSTALLER_BASENAME = $PreviousInstallerName
}

$Installer = Join-Path $DistPath ($InstallerBaseName + ".exe")
if (-not (Test-Path -LiteralPath $Installer)) { throw "Installer identificato non prodotto." }
& (Join-Path $PSScriptRoot "smoke_caronte_installer.ps1") -InstallerPath $Installer -ExpectedBuildManifest $BuildManifestPath | Out-Null

$InstallerItem = Get-Item -LiteralPath $Installer
$InstallerHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Installer).Hash
$ReleaseManifest = [ordered]@{
    installer_name = $InstallerItem.Name
    installer_size = $InstallerItem.Length
    installer_sha256 = $InstallerHash
    version = $BuildManifest.version
    git_commit = $BuildManifest.git_commit
    git_short_commit = $BuildManifest.git_short_commit
    source_branch = $BuildManifest.source_branch
    build_utc = $BuildManifest.build_utc
    build_id = $BuildManifest.build_id
    working_tree = $BuildManifest.working_tree
    oauth_client_included = $BuildManifest.oauth_client_included
    build_result = "PASS"
    smoke_build_result = "PASS"
    smoke_installer_result = "PASS"
    build_command = "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\build_caronte_installer.ps1"
}
$ReleaseManifestPath = Join-Path $DistPath ($InstallerBaseName + ".manifest.json")
$ReleaseJson = $ReleaseManifest | ConvertTo-Json
[IO.File]::WriteAllText($ReleaseManifestPath, $ReleaseJson, (New-Object Text.UTF8Encoding($false)))
Write-Output (Resolve-Path -LiteralPath $Installer).Path
Write-Output (Resolve-Path -LiteralPath $ReleaseManifestPath).Path
