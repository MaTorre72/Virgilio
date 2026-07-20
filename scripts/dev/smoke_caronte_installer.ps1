param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath,
    [Parameter(Mandatory = $true)]
    [string]$ExpectedBuildManifest
)

$ErrorActionPreference = "Stop"
$Installer = (Resolve-Path -LiteralPath $InstallerPath).Path
$Expected = Get-Content -Raw -LiteralPath (Resolve-Path -LiteralPath $ExpectedBuildManifest).Path | ConvertFrom-Json
$ExpectedName = "CaronteSetup-$($Expected.version)-$($Expected.git_short_commit).exe"
if ([IO.Path]::GetFileName($Installer) -ne $ExpectedName) { throw "Il nome installer non identifica versione e commit attesi." }
$SmokeId = [guid]::NewGuid().ToString("N")
$SmokeRoot = Join-Path ([IO.Path]::GetTempPath()) ("caronte-installer-smoke-" + $SmokeId)
$LocalRoot = Join-Path $SmokeRoot "local"
$RoamingRoot = Join-Path $SmokeRoot "roaming"
$ProgramRoot = Join-Path $LocalRoot "Programs\Caronte"
$StartRoot = Join-Path $RoamingRoot "Start Menu\Caronte"
$UninstallKey = "Software\VirgilioTests\Caronte-$SmokeId"
$RegistryPath = "Registry::HKEY_CURRENT_USER\$UninstallKey"
$Process = $null
$UninstallProcess = $null
$PreviousValues = @{
    LOCALAPPDATA = $env:LOCALAPPDATA; APPDATA = $env:APPDATA
    CARONTE_INSTALL_ROOT = $env:CARONTE_INSTALL_ROOT; CARONTE_START_MENU_ROOT = $env:CARONTE_START_MENU_ROOT
    CARONTE_UNINSTALL_KEY = $env:CARONTE_UNINSTALL_KEY; VIRTUAL_ENV = $env:VIRTUAL_ENV; PYTHONPATH = $env:PYTHONPATH
}
try {
    New-Item -ItemType Directory -Path $LocalRoot,$RoamingRoot | Out-Null
    $env:LOCALAPPDATA = $LocalRoot
    $env:APPDATA = $RoamingRoot
    $env:CARONTE_INSTALL_ROOT = $ProgramRoot
    $env:CARONTE_START_MENU_ROOT = $StartRoot
    $env:CARONTE_UNINSTALL_KEY = $UninstallKey
    $env:VIRTUAL_ENV = $null
    $env:PYTHONPATH = $null
    $InstallProcess = Start-Process -FilePath $Installer -ArgumentList "/S","/NO-LAUNCH" -PassThru -Wait
    if ($InstallProcess.ExitCode -ne 0) { throw "Installazione isolata non riuscita." }
    $InstalledExe = Join-Path $ProgramRoot "Caronte.exe"
    if (-not (Test-Path -LiteralPath $InstalledExe)) { throw "Caronte.exe non installato." }
    if (-not (Test-Path -LiteralPath (Join-Path $StartRoot "Caronte.lnk"))) { throw "Collegamento Start non creato." }
    if (-not (Test-Path -LiteralPath $RegistryPath)) { throw "Disinstallatore non registrato." }
    if ((Get-ItemPropertyValue -LiteralPath $RegistryPath -Name DisplayVersion) -ne $Expected.version) { throw "Versione di disinstallazione divergente." }
    if (Test-Path -LiteralPath (Join-Path $RoamingRoot "Caronte\config.yaml")) { throw "L'installer ha creato configurazione utente." }

    $Stdout = Join-Path $SmokeRoot "installed-build-info.json"
    $Stderr = Join-Path $SmokeRoot "installed-build-info.err"
    $InfoProcess = Start-Process -FilePath $InstalledExe -ArgumentList "--build-info" -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru -Wait
    if ($InfoProcess.ExitCode -ne 0) { throw "Build-info dell'eseguibile installato non riuscito." }
    $Actual = Get-Content -Raw -LiteralPath $Stdout | ConvertFrom-Json
    if ($Actual.version -ne $Expected.version) { throw "Versione installata divergente." }
    if ($Actual.commit -ne $Expected.git_short_commit) { throw "Commit installato divergente." }
    if ($Actual.build_id -ne $Expected.build_id) { throw "Build ID installato divergente." }
    $AboutProcess = Start-Process -FilePath $InstalledExe -ArgumentList "--smoke-about-available" -PassThru -Wait
    if ($AboutProcess.ExitCode -ne 0) { throw "Informazioni su Caronte non disponibili nell'installato." }

    $Process = Start-Process -FilePath $InstalledExe -PassThru
    $Deadline = [DateTime]::UtcNow.AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 250
        $Process.Refresh()
        if ($Process.HasExited) { throw "Caronte si e' chiuso prima del wizard." }
    } while ($Process.MainWindowTitle -ne "Caronte" -and [DateTime]::UtcNow -lt $Deadline)
    if ($Process.MainWindowTitle -ne "Caronte") { throw "La finestra Caronte non e' comparsa." }
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
    if (Test-Path -LiteralPath $RegistryPath) { throw "Registrazione di disinstallazione non rimossa." }
    if (-not (Test-Path -LiteralPath (Join-Path $ConfigRoot "config.yaml"))) { throw "Configurazione utente rimossa." }
    if (-not (Test-Path -LiteralPath (Join-Path $DataRoot "synthetic.txt"))) { throw "Dati utente rimossi." }
    Write-Output "Smoke installer: OK; nome, versione, commit, build ID, finestra, Informazioni e disinstallazione verificati"
}
finally {
    if ($null -ne $Process -and -not $Process.HasExited) { Stop-Process -Id $Process.Id -Force }
    if ($null -ne $UninstallProcess) {
        $Relocated = Join-Path ([IO.Path]::GetTempPath()) ("Caronte-uninstall-" + $UninstallProcess.Id + ".exe")
        if (Test-Path -LiteralPath $Relocated) { Remove-Item -LiteralPath $Relocated -Force }
    }
    if (Test-Path -LiteralPath $RegistryPath) { Remove-Item -LiteralPath $RegistryPath -Recurse -Force }
    foreach ($Name in $PreviousValues.Keys) {
        if ($null -eq $PreviousValues[$Name]) { Remove-Item -Path ("Env:" + $Name) -ErrorAction SilentlyContinue }
        else { Set-Item -Path ("Env:" + $Name) -Value $PreviousValues[$Name] }
    }
    Set-Location -LiteralPath ([IO.Path]::GetTempPath())
    if (Test-Path -LiteralPath $SmokeRoot) { Remove-Item -LiteralPath $SmokeRoot -Recurse -Force }
}
