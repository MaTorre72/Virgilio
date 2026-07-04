# Test report Virgilio - 2026-07-04

## 1. Sintesi

- esito complessivo: PASS_WITH_WARNINGS
- verificato: snapshot repo, runtime Python locale, suite `pytest local_connector`, smoke ufficiale `scripts/dev/smoke_local_connector.ps1`, `doctor` IMAP read-only, `pilot-run --dry-run`, `doctor-bucoliche` read-only, `pilot-preview`, `setup-bucoliche-test-sheet --dry-run`, due `pilot-run` reali consecutivi, toolchain `node/npm/clasp` via percorsi completi, verifica statica Apps Script, lessico documentale
- non verificato: deploy o sync Apps Script, `clasp push`, mailbox non di test, produzione Google/IMAP
- warning residui: `pip install -e .\local_connector` non e` autosufficiente offline finche` nel venv manca `setuptools`; le operazioni reali su Google restano limitate al test account usato in questo run

## 2. Contesto

- data/ora locale del run: `2026-07-04 10:57 +02:00`
- branch: `codex/v1.1-development`
- base locale: checkout con working tree pulito prima delle modifiche di questo run
- runtime Python verificato: `local_connector\.venv\Scripts\python.exe` (`Python 3.12.13`, `pip 25.0.1`)
- env locale caricata da: `local_connector\.env`
- nota operativa: i path relativi in `local_connector\.env` vanno risolti rispetto a `local_connector`
- toolchain Google locale: `node.exe v20.3.1`, `npm.cmd 9.6.7`, `clasp 3.3.0`

## 3. Test automatici offline

- comando: `local_connector\.venv\Scripts\python.exe -m pytest local_connector`
- esito: PASS
- risultato: `291 passed`
- smoke ufficiale:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_local_connector.ps1
```

- esito smoke: PASS
- risultato smoke: `291 passed in 47.33s` e `smoke_local_connector: OK`

## 4. Dry-run e readiness locali

- `doctor --config local_connector\accounts.local.yaml --human`: `READY`, con `imap=OK_READONLY`
- `pilot-run --config local_connector\accounts.local.yaml --dry-run --human`: `READY_DRY_RUN`, con `Bucoliche: eventi nuovi 0 / gia esportati 7`
- nel dry-run il completion ha trovato `1` messaggio completato e nessun ackabile staging message
- i comandi hanno funzionato solo dopo il caricamento della `.env` locale con risoluzione dei path relativi

## 5. Verifiche Bucoliche / Google

- `doctor-bucoliche --config local_connector\accounts.local.yaml --human`: `READY_WITH_WARNINGS`
- check passati: `config_section`, `adapter`, `enabled`, `spreadsheet_env`, `oauth_client_secret`, `oauth_token`, `spreadsheet_read`, `sheet:Bucoliche_Eventi`, `sheet:Bucoliche_Conflitti`
- warning atteso: `append capability not verified in read-only doctor`
- `pilot-preview --config local_connector\accounts.local.yaml --human`: `READY_WITH_WARNINGS`, `Eventi esportabili: 16`, `conflitti locali: 0`
- `setup-bucoliche-test-sheet --config local_connector\accounts.local.yaml --dry-run`: `DRY_RUN`
- il dry-run Bucoliche conferma gli header attesi per `Bucoliche_Eventi`, `Bucoliche_Conflitti`, `Bucoliche_Stato`

## 6. Collaudi reali

- primo `pilot-run --config local_connector\accounts.local.yaml --human`: `OK`
- output chiave del primo run:
  - `Pipeline: OK (completed)`
  - `Conflitti: 0`
  - `Bucoliche: eventi nuovi 16 / gia esportati 7`
  - `Stato: 7 righe aggiornate`
  - `Ack: 2 completati / 0 falliti / 0 pianificati / skipped (no_ackable_messages)`
- secondo `pilot-run --config local_connector\accounts.local.yaml --human`: `OK_NO_NEW_WORK`
- output chiave del secondo run:
  - `Bucoliche: eventi nuovi 0 / gia esportati 23`
  - `Stato: 7 righe aggiornate`
  - `Nessuna nuova azione: il secondo run conferma l'idempotenza locale`
- esito pratico: il mailbox di test e il flusso locale sono stati verificati davvero, con idempotenza confermata da due run consecutivi

## 7. Verifica clasp / Apps Script

- `node -v`: `v20.3.1`
- `npm -v`: `9.6.7`
- `clasp --version`: `3.3.0`
- `clasp status`: confermato via entrypoint esplicito
- stato `clasp`: mirror `apps_script\clasp` tracciato; untracked solo `.claspignore`
- deploy/push: non eseguiti

## 8. Fix applicati durante il run

- `doctor-bucoliche` ora accetta `--human`
- `doctor-bucoliche --human` usa un summary dedicato per la readiness Bucoliche, non il formatter del doctor IMAP
- test di regressione aggiunti per il comando Bucoliche CLI

## 9. Rischi e limiti residui

- `pip install -e .\local_connector` resta non autosufficiente offline senza `setuptools` nel venv
- non e` stato fatto alcun `clasp push` o deploy Apps Script
- nessuna verifica su mailbox o sheet non di test

## 10. Aggiornamento stato progetto

- report creato/aggiornato: `docs/TEST_REPORT_20260704.md`
- esito sintetico: `PASS_WITH_WARNINGS`
- blocchi pratici residui: solo l'install editable offline non autosufficiente e l'assenza di deploy/sync reali, non il flusso locale
