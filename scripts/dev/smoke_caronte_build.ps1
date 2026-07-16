param(
    [Parameter(Mandatory = $true)]
    [string]$BuildDirectory
)

$ErrorActionPreference = "Stop"
$Source = (Resolve-Path -LiteralPath $BuildDirectory).Path
$SourceExe = Join-Path $Source "Caronte.exe"
if (-not (Test-Path -LiteralPath $SourceExe)) {
    throw "Caronte.exe non trovato nella cartella indicata."
}

$SmokeRoot = Join-Path ([IO.Path]::GetTempPath()) ("caronte-build-smoke-" + [guid]::NewGuid().ToString("N"))
$CopiedBuild = Join-Path $SmokeRoot "Caronte"
$Process = $null
try {
    New-Item -ItemType Directory -Path $SmokeRoot | Out-Null
    Copy-Item -LiteralPath $Source -Destination $CopiedBuild -Recurse
    $env:VIRTUAL_ENV = $null
    $env:PYTHONPATH = $null
    Set-Location -LiteralPath $SmokeRoot
    $Process = Start-Process -FilePath (Join-Path $CopiedBuild "Caronte.exe") -PassThru
    $Deadline = [DateTime]::UtcNow.AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 250
        $Process.Refresh()
        if ($Process.HasExited) {
            throw "Caronte.exe si e' chiuso prima di mostrare la finestra."
        }
    } while ($Process.MainWindowTitle -ne "Caronte" -and [DateTime]::UtcNow -lt $Deadline)
    if ($Process.MainWindowTitle -ne "Caronte") {
        throw "La finestra Caronte non e' comparsa entro il tempo previsto."
    }
    Write-Output "Caronte.exe avviato dalla sola cartella copiata; titolo finestra: Caronte"
}
finally {
    if ($null -ne $Process -and -not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force
        $Process.WaitForExit()
    }
    Set-Location -LiteralPath ([IO.Path]::GetTempPath())
    if (Test-Path -LiteralPath $SmokeRoot) {
        Remove-Item -LiteralPath $SmokeRoot -Recurse -Force
    }
}
