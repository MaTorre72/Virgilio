# Test readiness Virgilio - 2026-07-04

## 1. Sintesi

- esito: PASS_WITH_WARNINGS
- il local connector e` pronto per collaudi reali sul mailbox di test
- la parte Bucoliche/Google e` stata verificata in sola lettura e con dry-run
- resta aperto solo il solito limite di packaging offline e l'assenza di deploy/sync reali

## 2. Cosa e` gia` verde

- `pytest local_connector`: `291 passed`
- `scripts/dev/smoke_local_connector.ps1`: `291 passed` e `smoke_local_connector: OK`
- `doctor --config local_connector\accounts.local.yaml --human`: `READY`
- `pilot-run --config local_connector\accounts.local.yaml --dry-run --human`: `READY_DRY_RUN`
- `doctor-bucoliche --config local_connector\accounts.local.yaml --human`: `READY_WITH_WARNINGS`
- `pilot-preview --config local_connector\accounts.local.yaml --human`: `READY_WITH_WARNINGS`
- `setup-bucoliche-test-sheet --config local_connector\accounts.local.yaml --dry-run`: `DRY_RUN`
- `pilot-run --config local_connector\accounts.local.yaml --human`: `OK`
- secondo `pilot-run --config local_connector\accounts.local.yaml --human`: `OK_NO_NEW_WORK`

## 3. Cosa e` stato sistemato

- documentazione riallineata sul runtime verificato: `local_connector\.venv\Scripts\python.exe`
- i path relativi in `local_connector\.env` sono stati gestiti rispetto a `local_connector`
- toolchain locale verificata fuori dal PATH del thread: `node.exe`, `npm.cmd`, `clasp`
- `clasp status` confermato via entrypoint esplicito
- il CLI `doctor-bucoliche` ora accetta `--human` e usa un summary dedicato alla readiness Bucoliche

## 4. Cosa resta aperto

- `pip install -e .\local_connector` non e` autosufficiente offline finche` il venv non contiene `setuptools`
- `clasp push` e qualsiasi deploy/sync Apps Script non sono stati eseguiti
- non e` stata toccata una mailbox non di test

## 5. Comandi pronti per Marco

### Caricamento env locale

Se lanci i comandi dal repo root, ricorda che questi valori di `local_connector\.env` vanno risolti rispetto a `local_connector`:

- `VIRGILIO_LOCAL_DATA_DIR`
- `VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH`
- `VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH`

### Collaudi locali

```powershell
cd C:\Users\Marco\Documents\Virgilio
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor --config local_connector\accounts.local.yaml --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-run --config local_connector\accounts.local.yaml --dry-run --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor-bucoliche --config local_connector\accounts.local.yaml --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-preview --config local_connector\accounts.local.yaml --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector setup-bucoliche-test-sheet --config local_connector\accounts.local.yaml --dry-run
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-run --config local_connector\accounts.local.yaml --human
```

### Smoke consigliato

```powershell
cd C:\Users\Marco\Documents\Virgilio
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_local_connector.ps1
```

### Tooling locale

```powershell
& 'C:\Program Files (x86)\nodejs\node.exe' -v
& 'C:\Program Files (x86)\nodejs\npm.cmd' -v
& 'C:\Program Files (x86)\nodejs\node.exe' 'C:\Users\Marco\AppData\Roaming\npm\node_modules\@google\clasp\build\src\index.js' --version
& 'C:\Program Files (x86)\nodejs\node.exe' 'C:\Users\Marco\AppData\Roaming\npm\node_modules\@google\clasp\build\src\index.js' status
```

## 6. Criteri per il prossimo passaggio

- il local connector e` gia` pronto per ulteriori run reali sul mailbox di test
- l'eventuale prossimo passo dipende solo dal perimetro che vuoi toccare: locale, Google-only o deploy Apps Script

## 7. Rischi residui

- l'install editable offline resta il punto piu` fragile
- `clasp` e` disponibile via percorso completo, ma non e` stata eseguita alcuna sincronizzazione live
- le verifiche su dati non di test restano fuori scope
