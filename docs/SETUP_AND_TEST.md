# Setup e test

## Setup locale

```powershell
cd "$env:USERPROFILE\Documents\Virgilio"
local_connector\.venv\Scripts\python.exe --version
```

Nel checkout verificato il runtime affidabile e` `local_connector\.venv\Scripts\python.exe`.
Il path `.\.venv\Scripts\python.exe` non e` presente in questo workspace e non va assunto come default.
Su questa macchina i binari locali trovati sono `C:\Program Files (x86)\nodejs\node.exe`, `C:\Program Files (x86)\nodejs\npm.cmd` e `$env:APPDATA\npm\clasp.cmd`. Se il PATH non li risolve, usa i percorsi completi.

Per l'install editable:

```powershell
local_connector\.venv\Scripts\python.exe -m pip install -e .\local_connector
```

Nota offline importante:

- il comando sopra richiede che il venv abbia gia` `setuptools` disponibile;
- in questo workspace `setuptools` non e` installato nel venv locale, quindi `pip install -e .\local_connector` non e` autosufficiente offline;
- `--no-build-isolation` non basta se `setuptools.build_meta` manca nel venv.

Per i test offline non e` necessario forzare l'install editable se si usa il percorso verificato sotto con `PYTHONPATH`.
Se carichi `local_connector\.env` dal repo root, normalizza `VIRGILIO_LOCAL_DATA_DIR` e i path OAuth rispetto a `local_connector` prima di lanciare i comandi.

Configurazioni reali devono stare solo in `.env` o in variabili ambiente locali, mai nel repository.

Per creare uno scheletro locale valido senza segreti nel file:

```powershell
local_connector\.venv\Scripts\python.exe -m virgilio_connector init-config --output accounts.local.yaml --email nome@azienda.it --staging-dir C:\Virgilio\staging
```

`--staging-dir` deve essere un path assoluto, per esempio `C:\Virgilio\staging`; i path relativi vengono rifiutati dal CLI.
Il comando genera un `accounts.local.yaml` con account, storage, Bucoliche e rules minime;
le credenziali restano solo come nomi di variabili d'ambiente da valorizzare localmente.

## Test Python

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
local_connector\.venv\Scripts\python.exe -m pytest local_connector
```

I test automatici devono restare offline: niente Gmail reale, Drive reale, Bucoliche reale, notifiche o credenziali.

## Smoke offline raccomandato

Il comando offline piu` robusto e consigliato per questo repo e`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\smoke_local_connector.ps1
```

Lo smoke:

- usa `local_connector\.venv\Scripts\python.exe` se presente;
- imposta `PYTHONPATH` verso `local_connector\src`;
- esegue la suite `pytest` del local connector;
- verifica `virgilio_connector --help` e `virgilio_connector pilot --help`;
- controlla che non siano tracciati file locali o segreti vietati;
- non esegue Gmail reale, Drive reale, Bucoliche reale o notifiche reali.

## Tooling locale

Per verificare la toolchain locale senza deploy:

```powershell
& 'C:\Program Files (x86)\nodejs\node.exe' -v
& 'C:\Program Files (x86)\nodejs\npm.cmd' -v
& 'C:\Program Files (x86)\nodejs\node.exe' '$env:APPDATA\npm\node_modules\@google\clasp\build\src\index.js' --version
& 'C:\Program Files (x86)\nodejs\node.exe' '$env:APPDATA\npm\node_modules\@google\clasp\build\src\index.js' status
```

Se `clasp.cmd` non parte dal PATH, la forma con `node.exe` e` quella verificata qui.

## Dry-run locale controllato

Dopo aver valorizzato le env IMAP richieste nella sessione PowerShell corrente:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor --config local_connector\accounts.local.yaml --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-run --config local_connector\accounts.local.yaml --dry-run --human
```

Questi restano controlli locali. `pilot-run` senza `--dry-run` non e` un test automatico.
Nel checkout verificato sono stati eseguiti anche `doctor-bucoliche --human`, `pilot-preview --human`, `setup-bucoliche-test-sheet --dry-run` e due `pilot-run --human` consecutivi sul mailbox di test.

## Test Apps Script

Eseguire solo test puri o mockabili dall'editor Apps Script. I test che richiedono Drive, Gmail, Bucoliche o deployment reale vanno trattati come collaudi manuali separati.

Prima di `caronteTest()` e `caronteTestFinale()` verificare nelle Script Properties gli ID operativi condivisi: `VIRGILIO_BUCOLICHE_SPREADSHEET_ID`, `VIRGILIO_BUCOLICHE_TAB`, `VIRGILIO_EMPIREO_ID`, `VIRGILIO_ADAMO_ID`, `VIRGILIO_LIMBO_ID`, `VIRGILIO_INBOX_SPREADSHEET_ID`, `VIRGILIO_INBOX_SHEET_NAME`, `VIRGILIO_INTAKE_TEST_SPREADSHEET_ID`, `VIRGILIO_INTAKE_TEST_SHEET_NAME`.

## Collaudi reali

I percorsi che escono dal dry-run (`pilot-run` senza `--dry-run` e, nel profilo Google-only, `clasp push`) sono collaudi reali, non test automatici.

Ogni collaudo reale deve indicare:

- branch e commit;
- account/cartella di test;
- comando eseguito;
- risposta ricevuta;
- conferma degli effetti non prodotti;
- checklist manuale finale.
