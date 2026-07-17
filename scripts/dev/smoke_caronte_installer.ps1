param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath
)

$ErrorActionPreference = "Stop"
$Installer = (Resolve-Path -LiteralPath $InstallerPath).Path
$SmokeRoot = Join-Path ([IO.Path]::GetTempPath()) ("caronte-installer-smoke-" + [guid]::NewGuid().ToString("N"))
$LocalRoot = Join-Path $SmokeRoot "local"
$RoamingRoot = Join-Path $SmokeRoot "roaming"
$ProgramRoot = Join-Path $LocalRoot "Programs\Caronte"
$StartRoot = Join-Path $RoamingRoot "Start Menu\Caronte"
$Process = $null
$UninstallProcess = $null
$PreviousVirtualEnv = $env:VIRTUAL_ENV
$PreviousPythonPath = $env:PYTHONPATH
try {
    New-Item -ItemType Directory -Path $LocalRoot,$RoamingRoot | Out-Null
    $env:LOCALAPPDATA = $LocalRoot
    $env:APPDATA = $RoamingRoot
    $env:CARONTE_INSTALL_ROOT = $ProgramRoot
    $env:CARONTE_START_MENU_ROOT = $StartRoot
    $env:VIRTUAL_ENV = $null
    $env:PYTHONPATH = $null
    $InstallProcess = Start-Process -FilePath $Installer -ArgumentList "/S","/NO-LAUNCH" -PassThru -Wait
    if ($InstallProcess.ExitCode -ne 0) { throw "Installazione isolata non riuscita." }
    if (-not (Test-Path -LiteralPath (Join-Path $ProgramRoot "Caronte.exe"))) { throw "Caronte.exe non installato." }
    if (-not (Test-Path -LiteralPath (Join-Path $StartRoot "Caronte.lnk"))) { throw "Collegamento Start non creato." }
    if (-not (Test-Path -LiteralPath "Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\Caronte")) { throw "Disinstallatore non registrato." }
    if (Test-Path -LiteralPath (Join-Path $RoamingRoot "Caronte\config.yaml")) { throw "L'installer ha creato configurazione utente." }

    $Process = Start-Process -FilePath (Join-Path $ProgramRoot "Caronte.exe") -PassThru
    $Deadline = [DateTime]::UtcNow.AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 250
        $Process.Refresh()
        if ($Process.HasExited) { throw "Caronte si e' chiuso prima del wizard." }
    } while ($Process.MainWindowTitle -ne "Caronte" -and [DateTime]::UtcNow -lt $Deadline)
    if ($Process.MainWindowTitle -ne "Caronte") { throw "Il wizard di primo avvio non e' comparso." }
    Stop-Process -Id $Process.Id -Force
    $Process.WaitForExit()
    $Process = $null

    $ConfigRoot = Join-Path $RoamingRoot "Caronte"
    $DataRoot = Join-Path $LocalRoot "Caronte"
    New-Item -ItemType Directory -Path $ConfigRoot,$DataRoot | Out-Null
    Set-Content -LiteralPath (Join-Path $ConfigRoot "config.yaml") -Value "synthetic: true"
    Set-Content -LiteralPath (Join-Path $DataRoot "synthetic.txt") -Value "synthetic"
    $Uninstaller = Join-Path $ProgramRoot "DisinstallaCaronte.exe"
    $UninstallProcess = Start-Process -FilePath $Uninstaller -ArgumentList "/UNINSTALL","/S" -PassThru -Wait
    if ($UninstallProcess.ExitCode -ne 0) { throw "Avvio disinstallazione non riuscito." }
    $Deadline = [DateTime]::UtcNow.AddSeconds(20)
    while ((Test-Path -LiteralPath $ProgramRoot) -and [DateTime]::UtcNow -lt $Deadline) { Start-Sleep -Milliseconds 250 }
    if (Test-Path -LiteralPath $ProgramRoot) { throw "Programma non rimosso." }
    if (Test-Path -LiteralPath $StartRoot) { throw "Collegamento Start non rimosso." }
    if (Test-Path -LiteralPath "Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\Caronte") { throw "Registrazione di disinstallazione non rimossa." }
    if (-not (Test-Path -LiteralPath (Join-Path $ConfigRoot "config.yaml"))) { throw "Configurazione utente rimossa." }
    if (-not (Test-Path -LiteralPath (Join-Path $DataRoot "synthetic.txt"))) { throw "Dati utente rimossi." }
    Write-Output "Installer, collegamento Start, primo avvio e disinstallazione isolata: OK; dati utente preservati"
}
finally {
    if ($null -ne $Process -and -not $Process.HasExited) { Stop-Process -Id $Process.Id -Force }
    if ($null -ne $UninstallProcess) {
        $Relocated = Join-Path ([IO.Path]::GetTempPath()) ("Caronte-uninstall-" + $UninstallProcess.Id + ".exe")
        if (Test-Path -LiteralPath $Relocated) { Remove-Item -LiteralPath $Relocated -Force }
    }
    $env:CARONTE_INSTALL_ROOT = $null
    $env:CARONTE_START_MENU_ROOT = $null
    $env:VIRTUAL_ENV = $PreviousVirtualEnv
    $env:PYTHONPATH = $PreviousPythonPath
    Set-Location -LiteralPath ([IO.Path]::GetTempPath())
    if (Test-Path -LiteralPath $SmokeRoot) { Remove-Item -LiteralPath $SmokeRoot -Recurse -Force }
}
