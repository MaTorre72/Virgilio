# Test report Virgilio - 2026-07-04

## 1. Sintesi

- esito complessivo: PASS_WITH_WARNINGS
- verificato: snapshot repo, runtime Python locale, suite `pytest local_connector`, smoke ufficiale `scripts/dev/smoke_local_connector.ps1`, help CLI `virgilio_connector`, `doctor`/`pilot-run --dry-run` con config locale, presenza e analisi statica Apps Script, lessico documentale
- non verificato: run reali senza `--dry-run`, deploy o sync Apps Script, accesso Gmail/Drive/Bucoliche/Chat/Telegram reali, `clasp status`
- blocchi principali: `pip install -e .\local_connector` non offline per dipendenza build `setuptools>=68`; `doctor` e `pilot-run --dry-run` bloccati da env IMAP mancanti; `npm` e `clasp` non disponibili nel PATH/bundle corrente

## 2. Contesto

- data/ora locale: `2026-07-04 09:36:52 +02:00`
- branch: `codex/v1.1-development`
- commit: `6f3db13185cf925fd56cc1978967ee9d2d33d674` (`6f3db13 docs: record v1.1.3 backlog exhaustion`)
- working tree iniziale: pulito (`git status --short` vuoto)
- sistema operativo: `platform win32` rilevato da `pytest`; query CIM bloccata da permessi sandbox
- ambiente Python:
  - `python --version`: non disponibile nel PATH corrente
  - `.\.venv\Scripts\python.exe --version`: path non esistente nel workspace
  - `local_connector\.venv\Scripts\python.exe --version`: `Python 3.12.13`
  - `local_connector\.venv\Scripts\python.exe -m pip --version`: `pip 25.0.1`
- ambiente Node/clasp:
  - `node -v`: non disponibile nel PATH corrente
  - bundle Codex: `C:\Users\Marco\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe` -> `v24.14.0`
  - `npm -v`: non disponibile nel PATH; `npm.cmd` non trovato nel bundle Node
  - `clasp --version`: non disponibile nel PATH
- struttura principale rilevata: `.github/`, `apps_script/`, `docs/`, `local_connector/`, `scripts/`
- file chiave presenti:
  - `README.md`
  - `AGENTS.md`
  - `docs/DEV_BACKLOG.md`
  - `docs/NEXT_CODEX_TASKS.md`
  - `docs/CODEX_STATE.md`
  - `docs/CHANGELOG_DEV.md`
  - `docs/SETUP_AND_TEST.md`
  - `local_connector/`
  - cartella Apps Script: `apps_script/`
  - `.clasp.json`

## 3. Test automatici Python

- comando documentato: `.\.venv\Scripts\python.exe -m pip install -e .\local_connector`
- esito comando documentato: BLOCKED offline
- motivo: `pip` tenta di scaricare build dependency `setuptools>=68`
- variante sicura tentata: `local_connector\.venv\Scripts\python.exe -m pip install --no-build-isolation -e .\local_connector`
- esito variante: FAIL
- errore principale: `BackendUnavailable: Cannot import 'setuptools.build_meta'`
- comando eseguito per la suite offline:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
$env:PYTEST_DEBUG_TEMPROOT='C:\Users\Marco\AppData\Local\Temp\virgilio-pytest-report'
& 'local_connector\.venv\Scripts\python.exe' -m pytest local_connector
```

- esito: PASS
- risultato: `289 passed in 33.91s`
- compatibilita` offline: SI, nessuna evidenza di chiamate reali durante la suite
- smoke finale eseguito:

```powershell
$env:PYTEST_DEBUG_TEMPROOT='C:\Users\Marco\AppData\Local\Temp\virgilio-smoke-report'
powershell -NoProfile -ExecutionPolicy Bypass -File 'scripts\dev\smoke_local_connector.ps1'
```

- esito smoke: PASS
- risultato smoke: `289 passed in 29.41s` e `smoke_local_connector: OK`

## 4. Verifiche CLI local connector

- comandi eseguiti:
  - `python -m virgilio_connector --help`
  - `python -m virgilio_connector doctor --help`
  - `python -m virgilio_connector pilot-run --help`
  - `python -m virgilio_connector init-config --help`
- runtime usato: `local_connector\.venv\Scripts\python.exe` con `PYTHONPATH=local_connector\src`
- esito: PASS
- osservazioni:
  - CLI principale caricata correttamente
  - presenti i comandi `doctor`, `pilot-run`, `pilot`, `init-config`
  - `init-config --help` conferma opzioni sicure per generare uno scheletro locale senza segreti

## 5. Dry-run Caronte locale

- config trovata: `local_connector\accounts.local.yaml`
- doctor eseguito:

```powershell
python -m virgilio_connector doctor --config local_connector\accounts.local.yaml --human
```

- esito doctor: BLOCKED
- output utile:
  - `Esito doctor: BLOCKED`
  - `Account casella_mail: user=MISSING, password=MISSING, imap=NOT_CHECKED`
  - `Errore: casella_mail: username_env missing`
  - `Errore: casella_mail: password_env missing`
- pilot-run dry-run eseguito:

```powershell
python -m virgilio_connector pilot-run --config local_connector\accounts.local.yaml --dry-run --human
```

- esito pilot-run dry-run: BLOCKED
- output utile:
  - `Configurazione: BLOCKED (BLOCKED)`
  - `Pipeline: OK (NOT_RUN)`
  - `Ack: 0 completati / 0 falliti / 0 pianificati / skipped (doctor_blocked)`
  - `Errore: casella_mail: username_env missing`
  - `Errore: casella_mail: password_env missing`
- nota: il comando ha generato un report locale automatico non tracciato in `.local_data/reports/pilot_run_v11_20260704_074006.json`
- stato sintetico: BLOCKED per configurazione incompleta, senza effetti reali
- prossima azione: valorizzare localmente le env IMAP richieste e rieseguire `doctor` e `pilot-run --dry-run`
- comando sicuro suggerito per generare uno scheletro senza segreti, non eseguito:

```powershell
virgilio init-config --output accounts.local.yaml --email nome@azienda.it --staging-dir C:\Virgilio\staging
```

## 6. Verifica clasp / Apps Script

- `node -v` nel PATH: non disponibile
- bundle Node Codex disponibile: `v24.14.0`
- `npm -v`: non disponibile
- `clasp --version`: non disponibile
- cartella Apps Script presente: `apps_script/src` e `apps_script/clasp`
- `.clasp.json` presente in root repo con:
  - `scriptId` configurato
  - `rootDir: apps_script\clasp`
- `clasp status`: non eseguito
- motivo: `clasp` non presente nell'ambiente corrente, quindi impossibile verificare login o stato sync senza installazione/login manuale
- push/deploy: non eseguiti

## 7. Verifica statica Apps Script

- file trovati in `apps_script/src`:
  - `anagrafiche.gs`
  - `bucoliche.gs`
  - `caronte.gs`
  - `caronte_bridge.gs`
  - `drive_staging_intake_test.gs`
  - `drive_staging_verify.gs`
  - `notifiche.gs`
  - `setup.gs`
  - `test.gs`
  - `virgilio_inbox.gs`
  - `webapp.gs`
  - `virgilio.html`
- funzioni/elementi chiave trovati:
  - `doGet(e)` in `webapp.gs`
  - `doPost(e)` in `caronte.gs`
  - `apriPraticaDaVirgilio(dati)` in `caronte.gs`
  - `creaCartellaPratica(...)` in `caronte.gs`
  - `registraSuBucoliche`, `registraErrore`, `registraConflitto` in `bucoliche.gs`
  - `avvisaChat`, `avvisaTelegram` in `notifiche.gs`
  - `Virgilio_Inbox` in `virgilio_inbox.gs`
  - bridge locale in `caronte_bridge.gs`
  - uso `GmailApp` in `caronte.gs`, `test.gs`
  - riferimenti a `Limbo` diffusi in `caronte.gs`, `notifiche.gs`, `test.gs`
- elementi mancanti o dubbi:
  - stringa `Da_archiviare` non trovata; il lessico corrente usa `Da archiviare` lato UX e `Virgilio_Inbox` lato tecnico
  - nessuna prova locale che i file `apps_script/src` o `apps_script/clasp` siano sincronizzati o deployati sul progetto Apps Script reale
- rischi di regressione osservabili:
  - presenza di test/harness storici in `test.gs` che citano Gmail, Drive, Chat, Telegram e `doPost` reale: da mantenere separati dai test offline
  - permanenza del termine tecnico storico `staging` in commenti/config e funzioni interne, coerente solo se resta fuori dalla UX

## 8. Verifica documentale e lessico

- coerenze:
  - `README.md`, `AGENTS.md` e `docs/ARCHITETTURA_UNIFICATA.md` descrivono il flusso unico `Limbo -> Da archiviare -> Form -> Pratica finale -> Registro`
  - `docs/ARCHITETTURA_UNIFICATA.md` esplicita che `Virgilio_Inbox` e` nome tecnico e `Da archiviare` e` nome UX
  - `README.md` e `docs/SETUP_AND_TEST.md` separano test controllati da collaudi reali
- uso accettabile tecnico:
  - `staging` come termine storico/tecnico
  - `Bucoliche_Eventi`, `Bucoliche_Stato`, `Bucoliche_Conflitti` come supporti tecnici
  - `manifest`, `fingerprint`, `SQLite` come dettagli diagnostici
- incoerenze o avvisi:
  - `docs/SETUP_AND_TEST.md` e `README.md` mostrano `.\.venv\Scripts\python.exe`, ma nel workspace verificato il runtime funzionante e` `local_connector\.venv\Scripts\python.exe`
  - il documento di setup propone `pip install -e .\local_connector`, ma offline oggi il comando non e` autosufficiente senza `setuptools`
- raccomandazioni:
  - chiarire nella documentazione che il venv operativo verificato puo` essere quello annidato in `local_connector\.venv`
  - documentare che l'install editable offline richiede `setuptools` gia` presente nel venv oppure una procedura alternativa locale

## 9. Collaudi reali da eseguire manualmente

- Collaudo reale A - Local connector
  - flusso: `IMAP -> Quarantena -> Scan -> Limbo -> Da archiviare -> Form -> Pratica finale -> Registro`
  - prerequisiti: mail di test, allegati non sensibili, cartella Limbo di test o controllata, account test, comando senza `--dry-run` autorizzato dall'utente
- Collaudo reale B - Google-only
  - flusso: `GmailApp -> Limbo -> Da archiviare -> Form -> Pratica finale -> Registro`
  - prerequisiti: progetto Apps Script collegato con `clasp` in stato noto, login manuale utente, contesto Google di test
- Collaudo reale C - Form
  - apertura senza `inbox_id`
  - apertura con `inbox_id`
  - archiviazione in `02_corrispondenza`
  - notifica Chat/Telegram
- Registro
  - verifica append-only degli eventi finali e coerenza tra esito inbox e audit
- Da archiviare
  - verifica del record tecnico `Virgilio_Inbox` e della resa UX `Da archiviare`

## 10. Prossime azioni consigliate

1. Rendere offline affidabile `pip install -e .\local_connector`, includendo `setuptools` nel venv o aggiornando la procedura documentata.
2. Chiarire in `docs/SETUP_AND_TEST.md` e `README.md` quale interpreter e` realmente atteso nel checkout corrente.
3. Valorizzare in locale le env IMAP richieste e rieseguire `doctor` e `pilot-run --dry-run`.
4. Installare o rendere disponibile `clasp` in un ambiente controllato e verificare `clasp status` senza push/deploy.
5. Pianificare un collaudo reale autorizzato per il profilo Local connector e uno per il profilo Google-only.

## 11. Allegati/log essenziali

- `pytest local_connector`: `289 passed in 33.91s`
- `smoke_local_connector.ps1`: `289 passed in 29.41s` + `smoke_local_connector: OK`
- `doctor --human`: `Esito doctor: BLOCKED` per `username_env missing` e `password_env missing`
- `pilot-run --dry-run --human`: `Esito finale: BLOCKED` per configurazione locale incompleta
- report locale dry-run: `.local_data/reports/pilot_run_v11_20260704_074006.json`
- `pip install -e .\local_connector`: fallito offline per tentativo di recuperare `setuptools>=68`

## 12. Aggiornamento stato progetto

- report creato: `docs/TEST_REPORT_20260704.md`
- esito sintetico: `PASS_WITH_WARNINGS`
- blocchi: install editable offline non autosufficiente; dry-run bloccato da env IMAP mancanti; `clasp` non disponibile nell'ambiente corrente
