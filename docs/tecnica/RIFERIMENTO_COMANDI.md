# Riferimento dei comandi

Questo documento elenca le superfici eseguibili di Virgilio 1.1. È un
riferimento per sviluppatori e amministratori: non è il manuale dell'utente e
non implica autorizzazione a contattare servizi reali.

Per prerequisiti e configurazione usa
[CONFIGURAZIONE_E_INTEGRAZIONI.md](CONFIGURAZIONE_E_INTEGRAZIONI.md); per
backup, reset, build e deployment usa
[OPERAZIONI_E_MANUTENZIONE.md](OPERAZIONI_E_MANUTENZIONE.md).

## Contesti di esecuzione

La stessa CLI può essere avviata in tre modi:

```powershell
# Checkout di sviluppo: forma più esplicita e riproducibile.
$env:PYTHONPATH = (Resolve-Path "local_connector\src").Path
$carontePython = (Resolve-Path "local_connector\.venv\Scripts\python.exe").Path
& $carontePython -m virgilio_connector --help

# Package installato in una venv: console script dichiarato nel pyproject.
local_connector\.venv\Scripts\virgilio.exe --help

# Distribuzione Caronte: senza argomenti apre la GUI; con un comando inoltra alla CLI.
$caronteExe = "$env:LOCALAPPDATA\Programs\Caronte\Caronte.exe"
& $caronteExe --build-info
& $caronteExe maintenance-gui
```

Negli esempi successivi `python -m virgilio_connector` indica il primo
contesto. In PowerShell sostituirlo con `& $carontePython -m
virgilio_connector` oppure con l'eseguibile installato appropriato.

Il file di configurazione va passato con un percorso assoluto quando il comando
deve sopravvivere a cambi di directory o a un task pianificato:

```powershell
$caronteConfig = (Resolve-Path "$env:APPDATA\Caronte\config.yaml").Path
& $carontePython -m virgilio_connector doctor --config $caronteConfig --human
```

## Convenzioni e sicurezza

La CLI produce JSON compatto per impostazione predefinita. Dove disponibile,
`--human` mostra un riepilogo leggibile. In generale:

- codice `0`: comando completato o stato ammesso;
- codice `1`: blocco o esito di dominio che richiede attenzione;
- codice `2`: argomento, configurazione o dipendenza non valida;
- codice `130`: `watch` interrotto da tastiera.

Quattro classi di effetto sono usate nelle tabelle:

| Classe | Significato |
| --- | --- |
| locale lettura | legge configurazione o stato senza modificare servizi esterni |
| locale scrittura | crea file, report, DB, quarantena o task sulla postazione |
| rete lettura | contatta IMAP/Google/endpoint senza mutazione intenzionale |
| esterno scrittura | modifica mailbox, Drive, Sheets, Apps Script o notifier |

`--dry-run` limita gli effetti del comando specifico, ma non garantisce assenza
di rete: per esempio una scansione IMAP deve comunque leggere la casella. I
test automatici offline sono gli script `pytest`, non i dry-run operativi.

## Aiuto e identità

```powershell
python -m virgilio_connector --help
python -m virgilio_connector <comando> --help
Caronte.exe --build-info
```

`--build-info` esiste soltanto nella distribuzione e restituisce versione,
commit breve, data UTC e Build ID del manifest incorporato. Non esegue la
pipeline.

La distribuzione espone anche `--smoke-about-available` e la modalità
`--demo --demo-screen=<schermata> [--demo-scale=<fattore>]`. Sono ingressi
interni per smoke e prove visuali sintetiche: non configurano una postazione e
non sono comandi operativi da distribuire agli utenti.

## Presentazioni

### `user-gui`

```powershell
python -m virgilio_connector user-gui [--config <config.yaml>]
```

Apre la presentazione utente `Caronte`. Senza `--config` usa
`%APPDATA%\Caronte\config.yaml`. L'eseguibile installato senza argomenti è la
forma ordinaria equivalente.

### `maintenance-gui`

```powershell
python -m virgilio_connector maintenance-gui [--config <config.yaml>]
```

Apre la presentazione separata `Caronte Manutenzione` per Registro, endpoint,
backup, integrità, report e reset. Non è la GUI legacy `gui`/`gui_*`, che non è
una superficie supportata della 1.1.

## Configurazione iniziale

### `init-config`

```powershell
python -m virgilio_connector init-config `
  --output C:\configurazioni\caronte.yaml `
  --email test@example.invalid `
  --staging-dir C:\Virgilio\Limbo `
  [--provider gmail_workspace|generic_imap] `
  [--account-alias alias] `
  [--imap-host host] [--imap-port 993] `
  [--input-folder nome] [--done-folder nome] [--error-folder nome] `
  [--enable-bucoliche] [--dry-run] [--force]
```

Genera uno scheletro strutturale senza segreti. `--staging-dir` deve essere
assoluto. `--dry-run` stampa il contenuto senza scrivere; senza `--force` un
file esistente non viene sovrascritto. Effetto: locale scrittura.

### `doctor`

```powershell
python -m virgilio_connector doctor --config <config.yaml> [--human]
```

Verifica account abilitati, riferimenti alle credenziali, apertura IMAP
read-only, scrivibilità dati/SQLite, Limbo e scanner. Può creare il layout dati
e un database iniziale; può contattare IMAP. Stati: `READY`,
`READY_WITH_WARNINGS`, `BLOCKED`.

## Pipeline locale

### Comandi per fase

| Comando | Sintassi minima | Effetto e uso |
| --- | --- | --- |
| `scan-imap-accounts` | `--config <file> [--dry-run]` | elenca messaggi pendenti per casella con accesso IMAP read-only; senza dry-run registra run e messaggi localmente |
| `process-imap-accounts` | `--config <file> [--dry-run]` | scarica gli allegati ammessi nella quarantena, applica policy, regole e scanner; il dry-run evita la persistenza locale ma legge IMAP |
| `stage-ready-attachments` | `--config <file> [--dry-run]` | copia allegati `ready` e manifest nel `storage.staging_dir`; solo file locali/sincronizzati |
| `complete-staged-messages` | `--config <file> [--dry-run]` | valuta messaggi con allegati staged e applica la strategia di completamento configurata; la modalità reale può scrivere IMAP se l'ack è abilitato |
| `ack-completed-messages` | `--config <file> [--dry-run]` | wrapper con gate espliciti per l'ack; richiede handoff Da archiviare, assenza conflitti e stati ammessi |

Per isolare un problema eseguire le fasi nell'ordine della tabella. Non usare
`process-imap-accounts` come sostituto della scansione diagnostica e non
abilitare l'ack durante il primo pilot.

### `run-local-pipeline`

```powershell
python -m virgilio_connector run-local-pipeline `
  --config <config.yaml> [--dry-run] [--human]
```

Orchestra acquisizione, quarantena, staging, verifica Drive, handoff a Da
archiviare e completamento usando i servizi condivisi. In modalità reale può
leggere IMAP, scrivere dati locali e contattare l'endpoint Apps Script; gli
effetti finali dipendono da configurazione e gate.

### `watch`

```powershell
python -m virgilio_connector watch `
  --config <config.yaml> `
  [--dry-run] [--human] `
  [--interval-seconds 300] [--max-cycles 0]
```

Ripete la pipeline. `--max-cycles 0` significa ciclo continuo; un valore
positivo limita l'esecuzione. `--interval-seconds` deve essere maggiore di
zero. Per una prova controllata:

```powershell
python -m virgilio_connector watch --config <config.yaml> `
  --dry-run --human --max-cycles 1
```

Le opzioni `--completion-followup-seconds`, `--completion-poll-seconds` e
`--progress-events` sono interne alla presentazione/worker e non costituiscono
un contratto operatore da impostare normalmente.

## Bridge Limbo -> Apps Script

Questi comandi sono superfici tecniche usate per verifiche mirate. La pipeline
ordinaria li compone tramite servizi applicativi.

### `stage-ready-files`

```powershell
python -m virgilio_connector stage-ready-files [--dry-run]
```

Wrapper compatibile che usa `VIRGILIO_LOCAL_DRIVE_STAGING_ENABLED` e
`VIRGILIO_LIMBO_LOCAL_SYNC_DIR`, non la sezione `storage` del file. Copia file
ready e manifest nella cartella sincronizzata. Preferire
`stage-ready-attachments --config` nel percorso 1.1.

### `send-caronte-dry-run`

```powershell
python -m virgilio_connector send-caronte-dry-run `
  --command-file <comando.json>
```

Invia al `VIRGILIO_CARONTE_DRY_RUN_URL` un contratto metadata-only. Non invia
byte o path e il ramo Apps Script non usa Drive, Gmail, Sheets o notifiche. È
comunque una richiesta di rete verso un deployment configurato.

### `verify-drive-staging`

```powershell
python -m virgilio_connector verify-drive-staging --manifest <file.manifest.json>
```

Chiede al `VIRGILIO_CARONTE_DRIVE_VERIFY_URL` di verificare visibilità,
unicità, dimensione e coerenza del file e del manifest nel Limbo Drive. È
read-only sul cloud; assenza di sincronizzazione produce un esito non pronto.

### `intake-drive-staging-test`

```powershell
python -m virgilio_connector intake-drive-staging-test `
  --manifest <file.manifest.json>
```

Invia il manifest al solo endpoint `VIRGILIO_CARONTE_INTAKE_TEST_URL`. Scrive
nel tab di collaudo esplicitamente configurato e rifiuta payload senza
`test_mode: true`. Non usarlo con asset di produzione.

### `intake-da-archiviare`

```powershell
python -m virgilio_connector intake-da-archiviare `
  --manifest <file.manifest.json> `
  --drive-file-id <id> `
  --manifest-file-id <id> `
  [--form-url <https://.../exec>]
```

Crea o aggiorna idempotentemente un record Da archiviare tramite
`VIRGILIO_CARONTE_INTAKE_URL` e `VIRGILIO_TOKEN`. Gli ID Drive sono obbligatori
e devono provenire dalla verifica cloud; non sostituirli con path locali. È una
scrittura esterna operativa.

## Pilot e readiness

| Comando | Sintassi | Scopo |
| --- | --- | --- |
| `pilot-check` | `--config <file>` | controlli strutturali di readiness e prerequisiti |
| `pilot-preview` | `--config <file> [--human]` | riepilogo di account, storage, Registro, ack e prossimo passo |
| `pilot-run-safe` | `--config <file> [--human]` | `pilot-check`, pipeline dry-run ed export dry-run; non abilita effetti reali |
| `pilot` | `--config <file> [--human]` | vista compatibile che unisce preview e `pilot-run-safe` |
| `pilot-run` | `--config <file> [--dry-run] [--human]` | orchestratore 1.1: doctor, pipeline, conflitti, export Registro e gate ack |

Sequenza consigliata da checkout:

```powershell
python -m virgilio_connector doctor --config <config.yaml> --human
python -m virgilio_connector pilot-preview --config <config.yaml> --human
python -m virgilio_connector pilot-run-safe --config <config.yaml> --human
python -m virgilio_connector pilot-run --config <config.yaml> --dry-run --human
```

I comandi di readiness possono leggere IMAP o verificare credenziali quando la
configurazione lo consente. `pilot-run` senza `--dry-run` è un'operazione reale,
non un test automatico. Produce un report `pilot_run_v11_*.json` nella
directory locale dei report.

## Stato, conflitti ed export

### `check-local-conflicts`

```powershell
python -m virgilio_connector check-local-conflicts --config <config.yaml>
```

Legge `state.db` e rileva duplicati e collisioni di fingerprint, hash, nome o
manifest. Non risolve né modifica lo stato. Ritorna codice `1` quando esistono
conflitti.

### `export-central-events`

```powershell
python -m virgilio_connector export-central-events `
  --config <config.yaml> [--format jsonl|csv]
```

Esporta la vista tecnica completa in `exports/central_events_<timestamp>`.
Effetto: locale scrittura. Il file può contenere metadati operativi e va
controllato prima di essere condiviso.

### `export-registro-events`

```powershell
python -m virgilio_connector export-registro-events `
  --config <config.yaml> [--format jsonl|csv]
```

Esporta la proiezione leggibile del Registro in
`exports/registro_events_<timestamp>`. Non scrive Google Sheets.

### `doctor-bucoliche`

```powershell
python -m virgilio_connector doctor-bucoliche `
  --config <config.yaml> [--human]
```

Valida la sezione `bucoliche`, credenziali disponibili e contratto del
Registro. Può ispezionare Google Sheets se configurato.

### `export-to-bucoliche`

```powershell
python -m virgilio_connector export-to-bucoliche `
  --config <config.yaml> [--dry-run]
```

Esporta gli eventi non ancora consegnati al tab append-only `bucoliche` e
registra localmente gli esiti. Senza `--dry-run` è una scrittura Google Sheets.

### `refresh-bucoliche-state`

```powershell
python -m virgilio_connector refresh-bucoliche-state `
  --config <config.yaml> [--dry-run]
```

Rigenera la vista di stato consolidata a partire dagli eventi. In dry-run
restituisce la preview senza scrivere; la modalità reale modifica il foglio di
stato gestito dall'adapter.

### `setup-bucoliche-test-sheet`

```powershell
python -m virgilio_connector setup-bucoliche-test-sheet `
  --config <config.yaml> [--dry-run]
```

Prepara esclusivamente il foglio di test previsto dalla configurazione.
Eseguire prima `--dry-run` e verificare che l'asset sia chiaramente TEST.

### `google-oauth-login`

```powershell
python -m virgilio_connector google-oauth-login --config <config.yaml>
```

Avvia il flusso OAuth locale usato dal percorso CLI `user_oauth_local` e crea o
aggiorna il token nel path dichiarato dalla configurazione ambiente. Apre il
browser, contatta Google e scrive materiale sensibile locale. Non è il percorso
ordinario della GUI installata, che usa Gestione credenziali Windows.

## Task Scheduler Windows

### `install-windows-task`

```powershell
python -m virgilio_connector install-windows-task `
  --config <config.yaml> `
  [--python-exe <python.exe>] `
  [--task-name "Virgilio Local Watch"] `
  [--interval-seconds 300] `
  [--dry-run] [--force] [--human]
```

Dal checkout costruisce un task `ONLOGON`, a privilegi limitati, che avvia
`watch` in una finestra PowerShell nascosta. Configurazione, Python e root del
repository devono esistere. Usare prima `--dry-run`; `--force` sostituisce un
task con lo stesso nome.

La distribuzione installata usa un piano equivalente basato su `Caronte.exe`,
governato dalla GUI, e non deve dipendere da Python o dal repository.

### `status-windows-task`

```powershell
python -m virgilio_connector status-windows-task `
  [--task-name "Virgilio Local Watch"] [--human]
```

Legge installazione, stato, ultima esecuzione, prossima esecuzione e risultato.
Non modifica il task.

### `uninstall-windows-task`

```powershell
python -m virgilio_connector uninstall-windows-task `
  [--task-name "Virgilio Local Watch"] --confirm [--human]
```

Rimuove il task identificato dal nome esatto. `--confirm` è obbligatorio. Non
rimuove configurazione, dati o credenziali.

## Reset locale

### `reset-local-state`

```powershell
python -m virgilio_connector reset-local-state `
  --backup --confirm [--human]
```

Azione distruttiva protetta. Acquisisce il lock, crea un backup verificato
file-per-file, elimina `state.db` e quarantena, ricrea il layout e preserva
configurazione, credenziali e `machine_id`. Entrambi i flag sono obbligatori;
se un processo possiede il lock il comando si ferma.

## Bootstrap e test di sviluppo

### Bootstrap

Da una clone pulita su Windows con Python 3.11 o successivo:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\bootstrap_local_connector.ps1
```

Lo script crea `local_connector\.venv`, installa il package editable con
l'extra `dev` dichiarato nel `pyproject.toml` e verifica l'help CLI. Per una
toolchain specifica usare `-Python C:\percorso\python.exe`.

### Test per livello

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\test_local_connector_level.ps1 -Level unit
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\test_local_connector_level.ps1 -Level contract
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\test_local_connector_level.ps1 -Level integration_offline
```

Ogni modulo di test appartiene a un solo livello. Tutti usano fixture
sintetiche e devono restare senza mail, Google, credenziali o notifiche reali.

### Smoke completo

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\smoke_local_connector.ps1
```

Esegue l'intera suite, verifica help CLI, file di governance e assenza di
segreti/local data tracciati. È il gate completo per codice o governance del
percorso locale.

## Build e installer

### Build one-folder

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\build_caronte.ps1 `
  [-PythonPath C:\percorso\python.exe] `
  [-OutputRoot C:\percorso\output] `
  [-GoogleOAuthClientPath C:\percorso-protetto\google_oauth_client.json] `
  [-HumanAcceptanceBuild]
```

Produce `Caronte.exe` e un manifest. `-HumanAcceptanceBuild` richiede tree
pulito e branch `codex/v1.1-development`.

### Smoke build

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\smoke_caronte_build.ps1 `
  -BuildDirectory local_connector\build-output\dist\Caronte `
  -ExpectedBuildManifest local_connector\build-output\metadata\build_manifest.json
```

### Build installer

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\build_caronte_installer.ps1 `
  [-PythonPath C:\percorso\python.exe] `
  [-OutputRoot C:\percorso\output] `
  [-GoogleOAuthClientPath C:\percorso-protetto\google_oauth_client.json]
```

Ricostruisce la build con gate di accettazione, esegue lo smoke build, genera
l'installer per utente, esegue lo smoke installer e scrive il manifest release
con SHA-256.

### Smoke installer isolato

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\smoke_caronte_installer.ps1 `
  -InstallerPath <CaronteSetup-versione-commit.exe> `
  -ExpectedBuildManifest local_connector\build-output\metadata\build_manifest.json
```

## Apps Script e `clasp`

Questi comandi appartengono al profilo Google e non vanno mescolati con lo
smoke Python:

```powershell
clasp --version
clasp status
clasp pull
clasp push
```

- `clasp status` è il controllo iniziale non mutante;
- `clasp pull` modifica il checkout e si esegue soltanto con tree pulito e
  progetto verificato;
- `clasp push` modifica il progetto Apps Script remoto e richiede un task o
  un'autorizzazione esplicita;
- il deployment web `/exec` è un'operazione successiva e distinta dal push.

Non versionare `.clasp.json`, `.clasprc.json`, token o Script Properties. Se
login, progetto o upstream sono inattesi, fermarsi prima di pull, push o deploy.

Funzioni amministrative da eseguire nell'editor Apps Script soltanto nel
contesto corretto:

| Funzione | Uso |
| --- | --- |
| `caronteStatoConfigurazione()` | presenza degli ID e valori operativi |
| `caronteStatoCredenziali()` | presenza delle credenziali senza mostrarle |
| `caronteSetupVirgilioInbox(id, nome)` | crea/consolida il tab Da archiviare |
| `caronteSetupTrigger()` | crea un unico trigger ogni 5 minuti |
| `caronteStatoTrigger()` | mostra i trigger Caronte |
| `caronteStopTrigger()` | mette in pausa il profilo Google-only |
| `caronteTest()` | collaudo manuale che può usare servizi reali; non è un test offline |
| `caronteTestFinale()` | collaudo reale completo, da eseguire solo con piano dedicato |

Le funzioni `testDriveStagingCloudVerify()` e gli altri test puri con fake non
contattano servizi; le funzioni di setup, trigger e collaudo possono invece
avere effetti reali. Verificare sempre l'implementazione e il contesto prima
dell'esecuzione.

## Sequenze pronte

### Clone pulita, solo sviluppo offline

```powershell
git clone <URL-DEL-REPOSITORY> Virgilio
Set-Location Virgilio
git switch codex/v1.1-development
git status --short
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\bootstrap_local_connector.ps1
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\smoke_local_connector.ps1
```

Non servono credenziali o servizi reali.

### Configurazione sintetica e validazione strutturale

```powershell
$env:PYTHONPATH = (Resolve-Path "local_connector\src").Path
$carontePython = (Resolve-Path "local_connector\.venv\Scripts\python.exe").Path
& $carontePython -m virgilio_connector init-config `
  --output local_connector\accounts.synthetic.yaml `
  --email test@example.invalid `
  --provider generic_imap `
  --staging-dir C:\Virgilio\Limbo-Sintetico
& $carontePython -m virgilio_connector pilot-preview `
  --config local_connector\accounts.synthetic.yaml --human
```

`doctor` non è incluso perché, con credenziali valorizzate, tenta la lettura
IMAP. Per test completamente offline usare fixture e suite automatica.

### Primo pilot autorizzato

```powershell
python -m virgilio_connector doctor --config <config.yaml> --human
python -m virgilio_connector pilot-preview --config <config.yaml> --human
python -m virgilio_connector pilot-run-safe --config <config.yaml> --human
python -m virgilio_connector pilot-run --config <config.yaml> --dry-run --human
```

Proseguire senza `--dry-run` soltanto dopo aver verificato account, Limbo,
Registro, endpoint, backup e assenza di conflitti. Mantenere `ack_enabled:
false` nel primo ciclo.
