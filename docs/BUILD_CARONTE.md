# Build autonoma di Caronte

## Prerequisiti

- Windows 11 x64;
- una distribuzione Python Windows completa, versione 3.11 o successiva, con Tcl/Tk;
- dipendenze del connettore e profilo di build installati con
  `python -m pip install -e ".[build]"` dalla cartella `local_connector`.

La Python embeddable non e` una toolchain valida per questa build perche` non
include Tcl/Tk. PyInstaller e` una dipendenza di sola build e non e` richiesto
sul computer che esegue Caronte.

## Comando

Dalla radice del repository:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\build_caronte.ps1
```

Lo script verifica Tcl/Tk, pulisce gli artefatti precedenti, genera il manifest
interno e crea la distribuzione one-folder in
`local_connector\build-output\dist\Caronte`. Per indicare una toolchain completa
diversa dalla venv predefinita usare `-PythonPath`.

Una build destinata al collaudo usa `-HumanAcceptanceBuild`: viene rifiutata se
il working tree non e` pulito, il commit non e` disponibile o la branch non e`
`codex/v1.1-development`.

L'identita della build si verifica senza aprire la GUI:

```powershell
local_connector\build-output\dist\Caronte\Caronte.exe --build-info
```

## Verifica autonoma

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_caronte_build.ps1 `
  -BuildDirectory local_connector\build-output\dist\Caronte `
  -ExpectedBuildManifest local_connector\build-output\metadata\build_manifest.json
```

Lo smoke copia soltanto la cartella prodotta in una directory temporanea,
rimuove i riferimenti all'ambiente di sviluppo, avvia `Caronte.exe`, verifica
il titolo `Caronte` e infine arresta il processo e rimuove la copia.

## Installer Windows

La pipeline release ricostruisce sempre la build autonoma nella stessa
esecuzione e poi crea il setup per utente con:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\build_caronte_installer.ps1
```

I risultati sono
`local_connector\build-output\installer\dist\CaronteSetup-<version>-<short-sha>.exe`
e il manifest JSON omonimo.
Installa il programma in `%LOCALAPPDATA%\Programs\Caronte`, crea il collegamento
Start e registra il disinstallatore per l'utente corrente. Configurazione e dati
restano rispettivamente in `%APPDATA%\Caronte` e `%LOCALAPPDATA%\Caronte` e non
vengono rimossi dalla disinstallazione.

Lo smoke isolato dell'intero ciclo e`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_caronte_installer.ps1 `
  -InstallerPath local_connector\build-output\installer\dist\CaronteSetup-<version>-<short-sha>.exe `
  -ExpectedBuildManifest local_connector\build-output\metadata\build_manifest.json
```

La pipeline installer esegue gia` smoke build e smoke installer, confrontando
versione, commit e build ID dell'eseguibile installato con il manifest atteso.
