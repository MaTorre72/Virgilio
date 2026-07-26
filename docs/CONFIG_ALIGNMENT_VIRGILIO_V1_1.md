# Config alignment Virgilio v1.1 - 2026-07-04

## 1. Esito

- esito: `PRONTO_CON_RISERVE`
- stato statico: `OK`
- stato live: `WARNING`
- blocchi trovati: nessuno nel codice sorgente e nella documentazione locale
- riserva principale: i valori live di Script Properties, URL e ID Google non sono leggibili offline in modo sicuro; sono stati verificati solo nomi, contratti e percorsi
- vincolo rispettato: nessun `.env`, `.clasprc.json`, trigger, deploy o ID live e` stato modificato

## 2. Fonti controllate

- `local_connector/.env.example`
- `local_connector/accounts.example.yaml`
- `local_connector/README.md`
- `local_connector/src/virgilio_connector/__main__.py`
- `local_connector/src/virgilio_connector/bucoliche.py`
- `local_connector/src/virgilio_connector/da_archiviare_intake.py`
- `local_connector/src/virgilio_connector/drive_staging_intake_test.py`
- `local_connector/src/virgilio_connector/drive_staging_verify.py`
- `local_connector/src/virgilio_connector/multi_account.py`
- `local_connector/src/virgilio_connector/pilot_readiness.py`
- `apps_script/src/caronte.gs`
- `apps_script/src/setup.gs`
- `apps_script/src/webapp.gs`
- `apps_script/src/virgilio_inbox.gs`
- `apps_script/src/drive_staging_verify.gs`
- `apps_script/src/drive_staging_intake_test.gs`
- `apps_script/src/notifiche.gs`
- `apps_script/src/bucoliche.gs`
- `docs/ARCHITETTURA_UNIFICATA.md`
- `docs/GAS_READINESS_20260704.md`
- `docs/GAS_PUSH_REPORT_20260704.md`

## 3. Mappa locale

- dry-run Caronte: `VIRGILIO_CARONTE_DRY_RUN_URL`
- verify Drive staging: `VIRGILIO_CARONTE_DRIVE_VERIFY_URL`
- intake test Drive staging: `VIRGILIO_CARONTE_INTAKE_TEST_URL`
- intake finale `Da archiviare`: `VIRGILIO_CARONTE_INTAKE_URL` e `VIRGILIO_TOKEN`
- staging locale: `VIRGILIO_LOCAL_DRIVE_STAGING_ENABLED` e `VIRGILIO_LOCAL_DRIVE_STAGING_DIR`
- Bucoliche: `VIRGILIO_BUCOLICHE_SPREADSHEET_ID`
- autenticazione Google: `VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON`, `VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH`, `VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH`
- account multi-mailbox: `VIRGILIO_IMAP_ACCOUNT_1_USERNAME`, `VIRGILIO_IMAP_ACCOUNT_1_PASSWORD`

## 4. Mappa GAS

- Script Properties operative: `VIRGILIO_BUCOLICHE_SPREADSHEET_ID`, `VIRGILIO_BUCOLICHE_TAB`, `VIRGILIO_EMPIREO_ID`, `VIRGILIO_ADAMO_ID`, `VIRGILIO_LIMBO_ID`, `VIRGILIO_TOKEN`, `WEBHOOK_CHAT`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `URL_FORM`
- Script Properties Drive/test: `VIRGILIO_LIMBO_ID`, `VIRGILIO_INBOX_SPREADSHEET_ID`, `VIRGILIO_INBOX_SHEET_NAME`
- azioni webapp: `local_imap_dry_run`, `verify_drive_staging`, `intake_drive_staging_test`, `intake_virgilio_inbox`
- tab operativi: `Virgilio_Inbox` e l'unico Registro `bucoliche`
- nomi UX: `Da archiviare`, `02_corrispondenza`

## 5. Confronto puntuale

| Area | Locale | GAS | Esito |
|---|---|---|---|
| Dry-run Caronte | `VIRGILIO_CARONTE_DRY_RUN_URL` verso `local_imap_dry_run` | `caronte.gs` intercetta `CARONTE_DRY_RUN_ACTION` | OK |
| Verify Drive staging | `VIRGILIO_CARONTE_DRIVE_VERIFY_URL` e manifest metadata-only | `VIRGILIO_LIMBO_ID` e `verify_drive_staging` | OK |
| Intake finale `Da archiviare` | `VIRGILIO_CARONTE_INTAKE_URL` e `VIRGILIO_TOKEN` | `VIRGILIO_INBOX_SPREADSHEET_ID`, `VIRGILIO_INBOX_SHEET_NAME`, `intake_virgilio_inbox` | OK con riserva live |
| Bucoliche | adapter append-only sul tab `bucoliche` a 17 colonne | `VIRGILIO_BUCOLICHE_SPREADSHEET_ID`, `VIRGILIO_BUCOLICHE_TAB` e stesso schema | OK |
| UX vs tab tecnico | `Da archiviare` nella documentazione operativa | `Virgilio_Inbox` come tab tecnico separato | OK |
| Notifiche | nessun segreto reale in repo | `WEBHOOK_CHAT`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `URL_FORM` | WARNING live non verificato |
| Staging locale | `VIRGILIO_LOCAL_DRIVE_STAGING_ENABLED` e `VIRGILIO_LOCAL_DRIVE_STAGING_DIR` | nessun equivalente diretto in GAS, per design | OK |

## 6. Risultati dell'allineamento

- `local_connector/.env.example` e` stato riallineato al flusso reale aggiungendo `VIRGILIO_CARONTE_INTAKE_URL` e `VIRGILIO_TOKEN`
- `accounts.example.yaml` e` coerente con i nomi attesi dal codice
- il contratto metadata-only rimane invariato: non si inviano byte, base64 o path locali ad Apps Script
- il tab tecnico `Virgilio_Inbox` resta separato dalla UX `Da archiviare`
- il vecchio endpoint diagnostico `Staging_Local_Test` non fa parte della topologia live
- il solo punto che non si puo` confermare offline e` il valore live delle Script Properties e degli ID Google

## 7. Rischi residui

- `VIRGILIO_INBOX_SPREADSHEET_ID` non ha fallback al foglio Bucoliche; per un setup pulito va impostato in modo esplicito
- `URL_FORM`, `WEBHOOK_CHAT`, `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` sono configurazioni live e non vanno esposte nei log o nei file di repo
- `docs/GAS_READINESS_20260704.md` resta uno snapshot pre-push NO GO e non va letto come stato corrente

## 8. Preflight offline consigliato

```powershell
$ErrorActionPreference = 'Stop'
Set-Location "$env:USERPROFILE\Documents\Virgilio"

$branch = git branch --show-current
if ($branch -ne 'codex/v1.1-development') {
  'BLOCKING: branch errata'
  exit 1
}

if (git status --short) {
  'BLOCKING: working tree non pulito'
  exit 1
}

$required = @(
  'VIRGILIO_CARONTE_DRY_RUN_URL',
  'VIRGILIO_CARONTE_DRIVE_VERIFY_URL',
  'VIRGILIO_CARONTE_INTAKE_TEST_URL',
  'VIRGILIO_CARONTE_INTAKE_URL',
  'VIRGILIO_TOKEN',
  'VIRGILIO_BUCOLICHE_SPREADSHEET_ID',
  'VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON',
  'VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH',
  'VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH',
  'VIRGILIO_LIMBO_ID',
  'VIRGILIO_INBOX_SPREADSHEET_ID',
  'VIRGILIO_INBOX_SHEET_NAME'
)

$missing = @()
foreach ($name in $required) {
  rg -n --fixed-strings $name local_connector apps_script docs | Out-Null
  if ($LASTEXITCODE -ne 0) {
    $missing += $name
  }
}

if ($missing.Count -gt 0) {
  'BLOCKING: nomi di configurazione mancanti'
  $missing | ForEach-Object { " - $_" }
  exit 1
}

& powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1
if ($LASTEXITCODE -ne 0) {
  'BLOCKING: smoke_local_connector fallito'
  exit 1
}

'WARNING: allineamento statico confermato; valori live di Script Properties e ID Google non letti offline'
```

## 9. Decisione finale

- esito operativo: `PRONTO_CON_RISERVE`
- pronto per collaudo locale: si
- pronto per collaudo live senza verifica manuale: no
- azione richiesta prima di un collaudo reale: confermare live `VIRGILIO_BUCOLICHE_SPREADSHEET_ID`, `VIRGILIO_BUCOLICHE_TAB`, `VIRGILIO_EMPIREO_ID`, `VIRGILIO_ADAMO_ID`, `VIRGILIO_LIMBO_ID`, `VIRGILIO_INBOX_SPREADSHEET_ID`, `VIRGILIO_INBOX_SHEET_NAME`, `URL_FORM` e le credenziali notifiche
