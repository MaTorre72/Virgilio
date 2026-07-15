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

## Primo avvio consigliato

Sequenza minima gia` coerente con il CLI attuale:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
$config = (Resolve-Path 'local_connector\accounts.local.yaml').Path
$python = (Resolve-Path 'local_connector\.venv\Scripts\python.exe').Path

local_connector\.venv\Scripts\python.exe -m virgilio_connector init-config --output local_connector\accounts.local.yaml --email nome@azienda.it --staging-dir C:\Virgilio\staging
local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor --config $config --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot --config $config --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-run --config $config --dry-run --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector install-windows-task --config $config --python-exe $python --dry-run
```

L'ordine corretto e`:

- `doctor` prima di ogni dry-run operativo;
- `pilot` per la vista sintetica del flusso;
- `pilot-run --dry-run` per la prova completa senza effetti;
- `install-windows-task --dry-run` solo dopo che la configurazione locale e` gia` valida.

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
$config = (Resolve-Path 'local_connector\accounts.local.yaml').Path
$python = (Resolve-Path 'local_connector\.venv\Scripts\python.exe').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor --config $config --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-preview --config $config --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-run --config $config --dry-run --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector watch --config $config --dry-run --human --max-cycles 1
local_connector\.venv\Scripts\python.exe -m virgilio_connector install-windows-task --config $config --python-exe $python --dry-run
```

Questi restano controlli locali. `pilot-run` senza `--dry-run` non e` un test automatico.
Nel checkout verificato sono stati eseguiti anche `doctor-bucoliche --human`, `pilot-preview --human`, `setup-bucoliche-test-sheet --dry-run` e due `pilot-run --human` consecutivi sul mailbox di test.

## Presentazione GUI legacy abbandonata

I moduli `gui`/`gui_*` non sono un percorso di setup o collaudo supportato e non
devono essere avviati, distribuiti o ampliati. `Caronte` e `Caronte Manutenzione`
restano applicazioni target con presentazioni nuove e separate. I test operativi
restano quelli CLI descritti in questo documento finche` `user_app` e la nuova
`maintenance_gui` non dispongono dei rispettivi collaudi dedicati.

## Reset locale sicuro

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector reset-local-state --backup --confirm
```

Il comando crea un backup automatico della cartella locale accanto allo stato corrente, poi ricrea il layout base e preserva `machine_id` quando presente. Senza `--backup` e `--confirm` non esegue cancellazioni.

## Avvio automatico su Windows 11

Per verificare prima il task pianificato senza registrarlo:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
$config = (Resolve-Path 'local_connector\accounts.local.yaml').Path
$python = (Resolve-Path 'local_connector\.venv\Scripts\python.exe').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector install-windows-task --config $config --python-exe $python --dry-run
```

Per creare davvero il task locale:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
$config = (Resolve-Path 'local_connector\accounts.local.yaml').Path
$python = (Resolve-Path 'local_connector\.venv\Scripts\python.exe').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector install-windows-task --config $config --python-exe $python --force
```

Il task usa Utilita` di Pianificazione con trigger `ONLOGON`, finestra PowerShell nascosta e comando `watch` sul checkout locale corrente. Non crea servizi residenti separati, non esegue installazioni silenziose e richiede path assoluti gia` presenti sul PC.

## Troubleshooting operativo

- Se `doctor` blocca su IMAP, correggi prima le env richieste: non passare a `pilot-run`.
- Se `storage.staging_dir` non esiste, crealo o correggilo nel file config; il CLI non usa fallback impliciti.
- Se `install-windows-task` fallisce su `config_path` o `python_exe`, passa path risolti con `Resolve-Path` come negli esempi sopra.
- Se `watch` serve solo come verifica, usa `--dry-run --max-cycles 1` per evitare loop lunghi.
- Se `clasp` non e` nel PATH, usa `node.exe` piu` il path completo di `@google\clasp\build\src\index.js`; evita installazioni globali improvvisate durante il collaudo.

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
