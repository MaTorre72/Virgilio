# Test readiness Virgilio - 2026-07-04

## 1. Sintesi

- esito: PASS_WITH_WARNINGS
- i test offline del local connector sono verdi
- l'ambiente e` stato chiarito sul runtime reale da usare
- il prossimo dry-run resta bloccato solo da interventi umani su env IMAP e tool `clasp`

## 2. Cosa e` gia` verde

- `pytest local_connector`: `289 passed`
- `scripts/dev/smoke_local_connector.ps1`: `289 passed` e `smoke_local_connector: OK`
- CLI `virgilio_connector` caricata correttamente
- Apps Script presente e verificato staticamente
- working tree iniziale del task: pulito

## 3. Cosa e` stato sistemato

- documentazione riallineata sul runtime verificato: `local_connector\.venv\Scripts\python.exe`
- documentazione aggiornata per chiarire che `.\.venv\Scripts\python.exe` non e` il default valido in questo checkout
- procedura di setup/test aggiornata per esplicitare che l'install editable offline richiede `setuptools` gia` presente nel venv
- smoke offline promosso come comando raccomandato per i test locali senza effetti reali
- preparati i comandi PowerShell sicuri per valorizzare le env IMAP richieste nella sessione corrente
- toolchain locale verificata fuori dal PATH del thread: `C:\Program Files (x86)\nodejs\node.exe` (`v20.3.1`), `C:\Program Files (x86)\nodejs\npm.cmd` (`9.6.7`), `C:\Users\Marco\AppData\Roaming\npm\clasp.cmd` (`3.3.0`)
- `clasp status` eseguito con l'entrypoint locale e allineato al mirror `apps_script\clasp`

## 4. Cosa resta bloccato per intervento umano

- env IMAP mancanti per `doctor` e `pilot-run --dry-run`
- il PATH del thread non risolve sempre `node`, `npm` e `clasp`; quando serve usare i percorsi completi
- per il collaudo reale serve ancora il tuo account IMAP di test e la password o app password

## 5. Comandi pronti per Marco

### Verifica env richieste dal file locale

```powershell
Select-String -Path .\local_connector\accounts.local.yaml -Pattern "username_env|password_env"
```

Valori richiesti dal file attuale:

- username: `VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME`
- password: `VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD`

### Impostazione temporanea nella sessione PowerShell corrente

```powershell
Set-Item Env:VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME "INSERIRE_EMAIL"
Set-Item Env:VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD "INSERIRE_PASSWORD_O_APP_PASSWORD"
```

Note:

- queste variabili valgono solo per la sessione PowerShell corrente
- per renderle persistenti usare variabili utente Windows
- non scrivere password in file versionati
- non committare `.env`

### Dry-run locale dopo le env IMAP

```powershell
cd C:\Users\Marco\Documents\Virgilio
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor --config local_connector\accounts.local.yaml --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-run --config local_connector\accounts.local.yaml --dry-run --human
```

### Smoke offline raccomandato

```powershell
cd C:\Users\Marco\Documents\Virgilio
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_local_connector.ps1
```

### Verifica Node/npm/clasp

```powershell
node -v
npm -v
npm install -g @google/clasp
clasp --version
clasp login
clasp status
```

Nota su `.clasp.json`:

- `rootDir` e` coerente con `apps_script\clasp`
- `scriptId` e` presente ma non serve ristamparlo qui
- `clasp status` e` gia` stato verificato localmente con il binario esplicito; se il PATH non lo risolve, usa i percorsi completi sopra

## 6. Criteri per passare al collaudo reale

- `doctor --config local_connector\accounts.local.yaml --human` senza errori bloccanti
- `pilot-run --config local_connector\accounts.local.yaml --dry-run --human` senza blocchi di configurazione
- smoke offline ancora verde dopo ogni intervento locale
- `clasp status` e` gia` verificato localmente; per il profilo Google-only resta solo il login manuale se serve sincronizzare il progetto
- conferma esplicita dell'utente prima di qualsiasi `pilot-run` senza `--dry-run`

## 7. Rischi residui

- finche` il venv locale non include `setuptools`, `pip install -e .\local_connector` non e` ripetibile offline da zero
- l'assenza di `clasp` impedisce di verificare localmente lo stato di sync Apps Script
- il dry-run IMAP non puo` avanzare senza credenziali locali o app password fornite dall'utente
- nessun collaudo reale e` stato eseguito in questo task, correttamente
