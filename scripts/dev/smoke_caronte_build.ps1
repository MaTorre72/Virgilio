param(
    [Parameter(Mandatory = $true)]
    [string]$BuildDirectory,
    [Parameter(Mandatory = $true)]
    [string]$ExpectedBuildManifest
)

$ErrorActionPreference = "Stop"
$Source = (Resolve-Path -LiteralPath $BuildDirectory).Path
$ExpectedPath = (Resolve-Path -LiteralPath $ExpectedBuildManifest).Path
$Expected = Get-Content -Raw -LiteralPath $ExpectedPath | ConvertFrom-Json
$SourceExe = Join-Path $Source "Caronte.exe"
if (-not (Test-Path -LiteralPath $SourceExe)) { throw "Caronte.exe non trovato nella cartella indicata." }

$SmokeRoot = Join-Path ([IO.Path]::GetTempPath()) ("caronte-build-smoke-" + [guid]::NewGuid().ToString("N"))
$CopiedBuild = Join-Path $SmokeRoot "Caronte"
$Process = $null
try {
    New-Item -ItemType Directory -Path $SmokeRoot | Out-Null
    Copy-Item -LiteralPath $Source -Destination $CopiedBuild -Recurse
    $env:VIRTUAL_ENV = $null
    $env:PYTHONPATH = $null
    Set-Location -LiteralPath $SmokeRoot
    $Stdout = Join-Path $SmokeRoot "build-info.json"
    $Stderr = Join-Path $SmokeRoot "build-info.err"
    $InfoProcess = Start-Process -FilePath (Join-Path $CopiedBuild "Caronte.exe") -ArgumentList "--build-info" -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru -Wait
    if ($InfoProcess.ExitCode -ne 0) { throw "Caronte.exe --build-info non riuscito." }
    $Actual = Get-Content -Raw -LiteralPath $Stdout | ConvertFrom-Json
    foreach ($Field in @("version", "commit", "build_utc", "build_id")) {
        $ExpectedValue = if ($Field -eq "commit") { $Expected.git_short_commit } else { $Expected.$Field }
        if ($Actual.$Field -ne $ExpectedValue) { throw "Build-info divergente sul campo $Field." }
    }
    $AboutProcess = Start-Process -FilePath (Join-Path $CopiedBuild "Caronte.exe") -ArgumentList "--smoke-about-available" -PassThru -Wait
    if ($AboutProcess.ExitCode -ne 0) { throw "Informazioni su Caronte non disponibili nella build." }
    $WorkerHelp = Join-Path $SmokeRoot "worker-help.txt"
    $WorkerError = Join-Path $SmokeRoot "worker-help.err"
    $WorkerProcess = Start-Process -FilePath (Join-Path $CopiedBuild "Caronte.exe") -ArgumentList "watch --help" -RedirectStandardOutput $WorkerHelp -RedirectStandardError $WorkerError -PassThru -Wait
    if ($WorkerProcess.ExitCode -ne 0) { throw "Il controllo automatico non e' avviabile dalla cartella copiata." }
    $Process = Start-Process -FilePath (Join-Path $CopiedBuild "Caronte.exe") -PassThru
    $Deadline = [DateTime]::UtcNow.AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 250
        $Process.Refresh()
        if ($Process.HasExited) { throw "Caronte.exe si e' chiuso prima di mostrare la finestra." }
    } while ($Process.MainWindowTitle -ne "Caronte" -and [DateTime]::UtcNow -lt $Deadline)
    if ($Process.MainWindowTitle -ne "Caronte") { throw "La finestra Caronte non e' comparsa entro il tempo previsto." }
    Write-Output "Smoke build: OK; identita, worker, finestra Caronte e Informazioni verificate"
}
finally {
    if ($null -ne $Process -and -not $Process.HasExited) { Stop-Process -Id $Process.Id -Force; $Process.WaitForExit() }
    Set-Location -LiteralPath ([IO.Path]::GetTempPath())
    if (Test-Path -LiteralPath $SmokeRoot) { Remove-Item -LiteralPath $SmokeRoot -Recurse -Force }
}
