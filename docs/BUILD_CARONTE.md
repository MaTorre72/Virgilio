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

Lo script verifica Tcl/Tk, pulisce il lavoro precedente e crea la distribuzione
one-folder in `local_connector\build-output\dist\Caronte`. Per indicare una
toolchain completa diversa dalla venv predefinita usare `-PythonPath`.

## Verifica autonoma

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_caronte_build.ps1 `
  -BuildDirectory local_connector\build-output\dist\Caronte
```

Lo smoke copia soltanto la cartella prodotta in una directory temporanea,
rimuove i riferimenti all'ambiente di sviluppo, avvia `Caronte.exe`, verifica
il titolo `Caronte` e infine arresta il processo e rimuove la copia.
