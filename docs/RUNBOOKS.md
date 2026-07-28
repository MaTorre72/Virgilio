# Runbook correnti

Questa e` la mappa operativa breve di Virgilio 1.1. Per architettura e confini
usa [ARCHITETTURA_UNIFICATA.md](ARCHITETTURA_UNIFICATA.md); le procedure sotto
non autorizzano servizi reali, deploy o modifiche a `main`.

## Onboarding da clone pulito

Prerequisiti: Windows 11, Git e Python 3.11 o successivo raggiungibili dal
`PATH`. Da PowerShell, usa questo unico percorso; non servono credenziali,
configurazioni o dati reali:

```powershell
git clone <URL-DEL-REPOSITORY> Virgilio
cd Virgilio
git switch codex/v1.1-development
git branch --show-current
git status --short
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\bootstrap_local_connector.ps1
local_connector\.venv\Scripts\python.exe -m virgilio_connector --help
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_local_connector.ps1
```

Il bootstrap crea `local_connector\.venv` e installa il package con l'extra
`dev` dichiarato in `local_connector\pyproject.toml`; non mantiene un secondo
elenco di dipendenze. Se `python` non identifica il runtime corretto, passalo
esplicitamente con `-Python C:\percorso\python.exe`.

La branch deve essere `codex/v1.1-development` o una derivata e il tree deve
essere compreso prima di modificarlo. Per creare in seguito una configurazione
sintetica locale:

```powershell
local_connector\.venv\Scripts\python.exe -m virgilio_connector init-config --output local_connector\accounts.local.yaml --email test@example.invalid --staging-dir C:\Virgilio\Limbo
```

Regole per task e commit: [`AGENTS.md`](../AGENTS.md) e
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
un task dedicato, backup e autorizzazione. `clasp push` e deploy non sono mai
parte di un test locale.

### Apps Script

La sorgente canonica vive in `apps_script/src`; `.clasp.json` resta locale e
non va versionato. Prima di modificare: verificare branch e tree, eseguire
`clasp status` e `clasp pull`, quindi comprendere il diff. `clasp push` richiede
sempre un task esplicito o una conferma dell'utente; mai stampare token o creare
workaround con credenziali. Se progetto, login o stato remoto sono inattesi,
fermarsi senza sincronizzare.

## Release desktop

La build e la verifica sono separate dalla pubblicazione:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\build_caronte_installer.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_caronte_installer.ps1 -InstallerPath local_connector\build-output\installer\dist\CaronteSetup-<version>-<short-sha>.exe -ExpectedBuildManifest local_connector\build-output\metadata\build_manifest.json
```

Prima della build release: branch prevista, tree pulito, versione e commit
identificati. Dopo la build: confrontare eseguibile, manifest, versione, commit,
Build ID e SHA-256. Il client OAuth Desktop si fornisce solo dalla posizione
protetta prevista e non viene versionato. Deve essere di tipo app Desktop e
viene passato alla build con `-GoogleOAuthClientPath`; i token utente restano
separati nel deposito protetto Windows. Build, tag, push, deploy e pubblicazione
richiedono ciascuno il task o l'autorizzazione pertinente.

Per una build autonoma usare `scripts/dev/build_caronte.ps1`; per l'installer
usare `scripts/dev/build_caronte_installer.ps1`. La toolchain deve essere Python
3.11+ completa con Tcl/Tk. Verificare sempre manifest, versione, commit, Build
ID, SHA-256 e gli smoke dedicati prima di pubblicare.

## Conflitti tra postazioni

Un `conflict_cross_machine` non viene risolto automaticamente. Fermare le
azioni irreversibili, confrontare gli eventi locali delle macchine coinvolte,
scegliere una sola sorgente autorevole e correggere soltanto quella non
autorevole. Non modificare a mano il Registro e conservare fingerprint,
macchine, decisione, motivazione e timestamp della verifica.

## Pulizia locale sicura

Cache pytest, `__pycache__`, ambienti virtuali e output sotto
`local_connector/build-output`, `artifacts` e `_staging` sono rigenerabili.
Non eliminare `.local_data`, `.env`, `accounts.local.yaml`, `.clasp.json` o
altri dati e configurazioni operative senza backup e task esplicito.
