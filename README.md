# Virgilio

Virgilio e' il progetto interno Sigma+ per guidare apertura pratiche, presa in carico allegati e tracciamento operativo.

## Stato v1.1 sperimentale

La v1.0 resta l'MVP Google Workspace mono-utente. La linea v1.1 consolida il lavoro sperimentale sul Local IMAP Connector e prepara un'architettura meno dipendente da Google Apps Script:

- **Virgilio**: interfaccia, guida e supervisione umana;
- **Caronte Locale**: motore operativo locale, multi-casella e provider-agnostico;
- **Apps Script**: adattatore Google opzionale, non nucleo definitivo;
- **Persistenza locale**: registro operativo primario del connettore locale;
- **Bucoliche**: output adapter ispezionabile, non database primario;
- **Drive Desktop**: storage adapter iniziale di test, non architettura definitiva.

La branch `codex/v1.1-development` serve a consolidare componenti gia' testati. Non introduce nuove funzioni operative.

## Profili operativi

| Profilo | Quando usarlo | Superficie | Vincoli |
|---|---|---|---|
| Google-only | se il task tocca `apps_script/src`, GmailApp o `clasp` | Apps Script canonico in `apps_script/src`, mono-account | resta nel perimetro Google Workspace |
| Local connector | se il task tocca `local_connector/src/virgilio_connector` o i test locali | motore locale, fixture e CLI, multi-casella via IMAP | resta offline, senza servizi reali |

Se il task passa da Apps Script o dal progetto Google, il profilo attivo e` Google-only. Se passa dal motore locale o dai test, il profilo attivo e` Local connector.
Dopo il collaudo, vale la stessa regola: Google-only per Apps Script e Google Workspace; Local connector per lavoro locale, offline e di test.

## Stato architetturale

Virgilio ha due ingressi tecnici e un solo flusso operativo: Acquisizione -> Quarantena locale eventuale -> Limbo Drive unico -> Da archiviare -> Form -> Pratica finale -> Registro. Nella UX la coda si chiama `Da archiviare`; `Virgilio_Inbox` resta il nome tecnico del tab. Google-only resta mono-account; Local connector puo` essere multi-casella e leggere anche una casella Google Workspace via IMAP. La sorgente canonica Apps Script vive in `apps_script/src` e `clasp` sincronizza direttamente quella cartella; il local connector resta separato, locale e testabile senza servizi reali.
Il riferimento condiviso per lessico e flusso e` [Architettura unificata](docs/ARCHITETTURA_UNIFICATA.md).

## Componenti

| Area | Percorso | Ruolo |
|---|---|---|
| Google-only sorgente | `apps_script/src/` | moduli Apps Script canonici, incluso `appsscript.json` |
| Google-only sync | `.clasp.json`, `clasp` | collega e pubblica direttamente `apps_script/src/` |
| Local connector | `local_connector/src/virgilio_connector/` | motore locale, offline e testabile |
| Test local connector | `local_connector/tests/` | fixture e test automatici |
| Documentazione | `docs/` | riferimento condiviso e backlog |
| Documenti storici | `docs/archive/` | conservati per audit |

## Confini v1.1

In questa fase non sono abilitati come comportamento produttivo:

- ack IMAP automatico;
- upload reale generalizzato;
- spostamento messaggi;
- scrittura Bucoliche reale dal flusso locale senza fase controllata;
- notifiche operative;
- multi-account completo;
- AI.

## Test locali

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
local_connector\.venv\Scripts\python.exe -m pytest local_connector
```

I test del connettore non devono usare credenziali reali, Gmail reale, Drive reale o Bucoliche reale.
Nel checkout verificato il runtime giusto e` `local_connector\.venv\Scripts\python.exe`; `.\.venv\Scripts\python.exe` non e` disponibile qui.
Su questa macchina i binari locali trovati sono `C:\Program Files (x86)\nodejs\node.exe`, `C:\Program Files (x86)\nodejs\npm.cmd` e `C:\Users\Marco\AppData\Roaming\npm\clasp.cmd`. Se il PATH non li risolve, usa i percorsi completi.
Se carichi `local_connector\.env` dal repo root, risolvi i path relativi rispetto a `local_connector` prima di lanciare i comandi: vale per `VIRGILIO_LOCAL_DATA_DIR` e per i path OAuth.

Se serve l'install editable:

```powershell
local_connector\.venv\Scripts\python.exe -m pip install -e .\local_connector
```

Offline questo comando richiede `setuptools` gia` presente nel venv locale. Se `setuptools.build_meta` manca, per test e smoke resta piu` robusto usare `PYTHONPATH=local_connector\src` e il comando smoke ufficiale.

## Avvio rapido locale

Sequenza minima per partire senza Gmail reale, Drive reale o deploy Google:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
$config = (Resolve-Path 'local_connector\accounts.local.yaml').Path
$python = (Resolve-Path 'local_connector\.venv\Scripts\python.exe').Path

local_connector\.venv\Scripts\python.exe -m virgilio_connector init-config --output local_connector\accounts.local.yaml --email nome@azienda.it --staging-dir C:\Virgilio\staging
local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor --config $config --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot --config $config --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-run --config $config --dry-run --human
```

Ordine operativo:

- `init-config` crea il file locale senza scrivere segreti.
- `doctor` controlla env, storage e prerequisiti.
- `pilot` mostra il percorso completo senza effetti operativi.
- `pilot-run --dry-run` prova la sequenza controllata fino all'export simulato.
- Lo smoke locale resta il gate finale prima di qualunque collaudo reale.

## Uso quotidiano locale

Per il lavoro giornaliero sul profilo locale:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
$config = (Resolve-Path 'local_connector\accounts.local.yaml').Path
$python = (Resolve-Path 'local_connector\.venv\Scripts\python.exe').Path

local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor --config $config --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-preview --config $config --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector watch --config $config --dry-run --human --max-cycles 1
local_connector\.venv\Scripts\python.exe -m virgilio_connector install-windows-task --config $config --python-exe $python --dry-run
```

- `pilot-preview` riassume account, eventi esportabili e conflitti senza eseguire la pipeline.
- `watch --dry-run --max-cycles 1` verifica il loop operativo locale in un solo ciclo.
- `install-windows-task --dry-run` mostra il task `Virgilio Local Watch` senza registrarlo.
- Solo dopo il dry-run puoi usare `install-windows-task --force` per l'avvio automatico su Windows 11.

## Troubleshooting rapido

- Se `doctor` segnala `storage.staging_dir`, usa un path assoluto gia` esistente come `C:\Virgilio\staging`.
- Se `init-config` rifiuta `--staging-dir`, il path non e` assoluto: correggilo prima di proseguire.
- Se `pip install -e .\local_connector` fallisce offline, continua con `PYTHONPATH=local_connector\src` e smoke ufficiale.
- Se `clasp` non e` nel PATH, usa i percorsi completi documentati sotto invece di inventare alias o copiare token.
- Se devi azzerare il solo stato locale, usa `reset-local-state --backup --confirm`; non cancellare `.local_data` a mano.

## Documentazione principale

- [Architettura](docs/ARCHITECTURE.md)
- [Architettura unificata](docs/ARCHITETTURA_UNIFICATA.md)
- [Caronte Locale](docs/LOCAL_CARONTE.md)
- [Setup e test](docs/SETUP_AND_TEST.md)
- [Roadmap v1.1](docs/ROADMAP_V1_1.md)
- [Decisioni](docs/DECISIONS.md)

## Principio operativo

**L'AI propone. Il tecnico valida. Il sistema registra.**

Ogni automazione critica deve restare verificabile, reversibile e tracciata.

## Sviluppo autonomo con Codex

Il ciclo autonomo e` governato da:

- `AGENTS.md`: regole permanenti e limiti operativi;
- `docs/DEV_BACKLOG.md`: ordine dei task e stato di avanzamento;
- `docs/DEFINITION_OF_DONE.md`: gate obbligatori;
- `docs/AUTONOMOUS_DEVELOPMENT.md`: protocollo di scelta, esecuzione e stop;
- `.github/codex/prompts/advance.md`: prompt per avanzare un task;
- `scripts/dev/smoke_local_connector.ps1`: suite, CLI e controllo segreti;
- `.github/workflows/local-connector-ci.yml`: verifica senza servizi reali.

Per il prossimo task autonomo usare il prompt `advance.md`, oppure chiedere "vai avanti".

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1
```

Verifica locale e test controllati:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector init-config --output accounts.local.yaml --email nome@azienda.it --staging-dir C:\Virgilio\staging
local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor --config local_connector\accounts.local.yaml --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot --config local_connector\accounts.local.yaml --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector run-local-pipeline --config local_connector\accounts.local.yaml --dry-run --human
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-run --config local_connector\accounts.local.yaml --dry-run --human
$config = (Resolve-Path 'local_connector\accounts.local.yaml').Path
$python = (Resolve-Path 'local_connector\.venv\Scripts\python.exe').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector install-windows-task --config $config --python-exe $python --dry-run
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1
```

`--staging-dir` deve essere un path assoluto, per esempio `C:\Virgilio\staging`; i path relativi vengono rifiutati dal CLI.
- `init-config` prepara il profilo locale.
- `doctor` controlla la configurazione.
- `pilot` mostra il flusso senza effetti operativi.
- `run-local-pipeline --dry-run` e `pilot-run --dry-run` restano test controllati.
- `install-windows-task` prepara o registra l'avvio automatico locale con Utilita` di Pianificazione su Windows 11.
- Lo smoke locale resta la verifica finale minima.
- Sul mailbox di test sono stati verificati anche `doctor-bucoliche --human`, `pilot-preview --human`, `setup-bucoliche-test-sheet --dry-run` e due `pilot-run --human` consecutivi per confermare l'idempotenza.

Per attivare l'avvio automatico dopo il dry-run:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
$config = (Resolve-Path 'local_connector\accounts.local.yaml').Path
$python = (Resolve-Path 'local_connector\.venv\Scripts\python.exe').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector install-windows-task --config $config --python-exe $python --force
```

Il comando registra un task utente `ONLOGON` chiamato `Virgilio Local Watch`, avvia `watch` in finestra nascosta e resta limitato al profilo locale corrente; non installa servizi Windows e non richiede deploy Google.

Collaudi reali:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector pilot-run --config local_connector\accounts.local.yaml --human
```

`pilot-run` senza `--dry-run` va usato solo su configurazioni di test gia' verificate.

Per ripulire lo stato locale senza perdere una copia automatica:

```powershell
$env:PYTHONPATH=(Resolve-Path 'local_connector\src').Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector reset-local-state --backup --confirm
```

Il comando crea un backup sibling di `.local_data`, poi ricrea il layout base e preserva `machine_id` quando presente. Senza `--backup` e `--confirm` il reset non parte.

Per verificare lo snapshot Apps Script locale senza deploy:

```powershell
& 'C:\Program Files (x86)\nodejs\node.exe' 'C:\Users\Marco\AppData\Roaming\npm\node_modules\@google\clasp\build\src\index.js' --version
& 'C:\Program Files (x86)\nodejs\node.exe' 'C:\Users\Marco\AppData\Roaming\npm\node_modules\@google\clasp\build\src\index.js' status
```

`clasp status` conferma l'allineamento locale del progetto in `apps_script/src` e non richiede deploy.
