# Runbook correnti

Questa e` la mappa operativa breve di Virgilio 1.1. Per architettura e confini
usa [ARCHITETTURA_UNIFICATA.md](ARCHITETTURA_UNIFICATA.md); le procedure sotto
non autorizzano servizi reali, deploy o modifiche a `main`.

## Setup e sviluppo locale

Da PowerShell, nella radice del repository:

```powershell
git branch --show-current
git status --short
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector --help
```

La branch deve essere `codex/v1.1-development` o una derivata e il tree deve
essere compreso prima di modificarlo. Configurazioni, credenziali e dati reali
restano fuori dal repository. Per creare una configurazione sintetica locale:

```powershell
local_connector\.venv\Scripts\python.exe -m virgilio_connector init-config --output local_connector\accounts.local.yaml --email test@example.invalid --staging-dir C:\Virgilio\Limbo
```

Dettagli e prerequisiti: [SETUP_AND_TEST.md](SETUP_AND_TEST.md). Regole per task
e commit: [`AGENTS.md`](../AGENTS.md) e
[DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md).

## Test

Eseguire prima il test mirato al file o servizio modificato, poi la relativa
area. Il gate completo locale, richiesto quando si toccano codice o governance,
e`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_local_connector.ps1
```

Lo smoke usa fixture sintetiche e non deve contattare mail, Google, Drive,
notifiche o altri servizi reali. La struttura della suite e` descritta in
[`local_connector/tests/README.md`](../local_connector/tests/README.md).

## Operazioni

- **Caronte** (`virgilio_connector.user_app`) e` l'applicazione ordinaria:
  configurazione guidata, controllo manuale o continuo, stato e attivita`.
- **Caronte Manutenzione** (`virgilio_connector.maintenance_gui`) e` separata:
  diagnostica tecnica, backup, integrita` e reset controllato.
- La CLI e` destinata a sviluppo e automazione; non e` una terza GUI e non va
  tradotta automaticamente in pulsanti.

Reset, modifiche Gmail, operazioni Apps Script e altri effetti reali richiedono
un task dedicato, backup e autorizzazione. Il workflow Google-only e` in
[CLASP_WORKFLOW.md](CLASP_WORKFLOW.md); `clasp push` e deploy non sono mai parte
di un test locale.

## Release desktop

La build e la verifica sono separate dalla pubblicazione:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\build_caronte_installer.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_caronte_installer.ps1 -InstallerPath local_connector\build-output\installer\dist\CaronteSetup-<version>-<short-sha>.exe -ExpectedBuildManifest local_connector\build-output\metadata\build_manifest.json
```

Prima della build release: branch prevista, tree pulito, versione e commit
identificati. Dopo la build: confrontare eseguibile, manifest, versione, commit,
Build ID e SHA-256. Il client OAuth Desktop si fornisce solo dalla posizione
protetta prevista e non viene versionato. I dettagli sono in
[BUILD_CARONTE.md](BUILD_CARONTE.md) e
[GOOGLE_OAUTH_DESKTOP.md](GOOGLE_OAUTH_DESKTOP.md). Build, tag, push, deploy e
pubblicazione richiedono ciascuno il task o l'autorizzazione pertinente.
