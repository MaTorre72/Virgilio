# Installazione, dipendenze e comandi

## Prerequisiti

- Windows 11 x64;
- Git;
- Python 3.11 o successivo; per la build serve una distribuzione completa con
  Tcl/Tk;
- Google Drive per desktop per il Limbo;
- casella IMAP e credenziali nel deposito protetto locale;
- client OAuth Desktop autorizzato per Gmail/Google Workspace;
- deployment Apps Script e tab canonici configurati per l'uso operativo.

Le dipendenze Python sono dichiarate in `local_connector/pyproject.toml`:
`google-auth`, `google-auth-oauthlib`, `requests` e `tzdata`. Gli extra `dev` e
`build` aggiungono rispettivamente pytest e PyInstaller.

## Setup sviluppatore

```powershell
git clone <URL-REPOSITORY> Virgilio
cd Virgilio
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/bootstrap_local_connector.ps1
local_connector\.venv\Scripts\python.exe -m virgilio_connector --help
```

Il bootstrap crea `local_connector/.venv` e installa il package dalla sola
dichiarazione `pyproject.toml`.

## Comandi principali

```powershell
# Diagnosi configurazione
local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor --config <config> --human

# Controllo manuale
local_connector\.venv\Scripts\python.exe -m virgilio_connector watch --config <config> --max-cycles 1

# Smoke offline completo
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1

# Livelli separati
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/test_local_connector_level.ps1 -Level unit
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/test_local_connector_level.ps1 -Level contract
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/test_local_connector_level.ps1 -Level integration_offline
```

## Build e installer

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/build_caronte.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/build_caronte_installer.ps1
```

Prima della pubblicazione verificare versione, commit, Build ID, manifest,
SHA-256, smoke build e smoke installer. Il client OAuth viene fornito alla build
da un percorso protetto con `-GoogleOAuthClientPath` e non viene versionato.

## Apps Script

La sorgente canonica vive in `apps_script/src`. Verificare branch, tree e
progetto con `clasp status`; eseguire `clasp pull` prima delle modifiche.
`clasp push` e deploy richiedono sempre un task o un'autorizzazione esplicita.
Non stampare token e non versionare `.clasp.json` o `.clasprc.json`.

## File locali

Sono rigenerabili: cache pytest, `__pycache__`, ambienti virtuali,
`local_connector/build-output`, `artifacts` e `_staging`.
Non eliminare senza backup: `.local_data`, `.env`, `accounts.local.yaml`,
configurazioni, credenziali e stato operativo.
