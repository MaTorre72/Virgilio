# Virgilio Local Connector

Skeleton Python del connettore locale di ingresso per Virgilio.

## Stato

Il package contiene esclusivamente logica locale, astratta e simulata:

- modelli immutabili del contratto JSON con Caronte;
- parsing e serializzazione JSON;
- regola prudenziale per autorizzare un futuro ack;
- sanitizzazione nomi, SHA-256 e policy estensioni;
- macchina a stati della quarantena;
- porte astratte per mailbox, antivirus e Caronte;
- persistenza tecnica SQLite in `state.db`;
- orchestratore di un ciclo completo e adapter finti in memoria;
- test automatici senza rete.

Contiene una connessione IMAP4/SSL strettamente read-only per LC3. **Non contiene
chiamate HTTP, esecuzione antivirus, credenziali o operazioni IMAP di scrittura.**

## Confini

La micro-fase corrente si limita a lettura IMAP, valutazione deterministica e
quarantena locale. Non chiama Caronte, non carica su Drive e non esegue ack.

Restano in Apps Script Drive, Limbo Drive, Bucoliche, notifiche, pratiche e nucleo operativo Caronte.

## State database

`StateStore` usa SQLite standard library con schema versionato, WAL, foreign key e transazioni atomiche.

Esempio locale:

```python
from virgilio_connector import StateStore

store = StateStore("state.db")
store.initialize()
assert store.integrity_check()
```

`state.db` e i sidecar SQLite sono esclusi da Git. Il database non conserva credenziali, byte degli allegati o payload completi.

Dettagli: [`../docs/STATE_DB.md`](../docs/STATE_DB.md).

## Struttura

```text
local_connector/
  pyproject.toml
  src/virgilio_connector/
    ack.py
    contract.py
    files.py
    models.py
    policy.py
    ports.py
    quarantine.py
    state_db.py
    state_models.py
    orchestrator.py
    in_memory.py
  tests/
    test_*.py
```

## Test

Da `local_connector/`, con Python 3.11 o successivo:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -p 'test_*.py' -v
```

Non e' necessario installare dipendenze esterne. I test SQLite usano soltanto directory temporanee.

## Documentazione

- [`../docs/LOCAL_IMAP_CONNECTOR.md`](../docs/LOCAL_IMAP_CONNECTOR.md)
- [`../docs/CONTRATTO_DATI_CARONTE.md`](../docs/CONTRATTO_DATI_CARONTE.md)
- [`../docs/QUARANTENA_LOCALE.md`](../docs/QUARANTENA_LOCALE.md)
- [`../docs/STATE_DB.md`](../docs/STATE_DB.md)

## Simulazione offline

`ConnectorOrchestrator.run_once()` collega le porte mailbox, antivirus e Caronte.
Gli adapter in `in_memory.py` permettono di verificare l'intero ciclo senza rete:
registrazione, quarantena, policy, scansione, comando, conferma Limbo Drive e ack.
L'ack resta bloccato se Caronte non conferma almeno un allegato con hash e ID Drive.

La suite include inoltre email `.eml` generate con indirizzi `example.invalid` e
allegati sintetici. Copre messaggi con PDF, allegati misti, solo testo e polling
ripetuti; nessuna fixture contiene email, indirizzi o documenti reali.

## Prova IMAP read-only

### Configurazione `.env`

Copiare `.env.example` in `.env` e sostituire i soli valori locali. `.env`,
`.local_data/`, database, log e file temporanei sono esclusi da Git. Non usare
credenziali della casella principale: predisporre un account e messaggi fittizi.

### Dry-run

Il dry-run legge la cartella con `BODY.PEEK[]`, mostra le decisioni della policy e
non crea `.local_data`, file o database:

```powershell
$env:PYTHONPATH='src'
python scripts/imap_readonly_probe.py --dry-run
```

### Download controllato in quarantena

Dopo aver verificato manualmente il dry-run:

```powershell
$env:PYTHONPATH='src'
python scripts/imap_readonly_probe.py --download
```

La struttura generata e' `.local_data/quarantine/{incoming,rejected,ready}` con
`.local_data/logs` e `.local_data/state.db`. In questa fase vengono scritti solo
gli allegati ammessi dentro `incoming`.

## Scan multi-account read-only

La linea v1.1 introduce una configurazione locale multi-account. Copiare
`accounts.example.yaml` fuori dal repository o in un percorso locale ignorato e
compilare solo nomi di variabili d'ambiente, mai password in chiaro nel file.

Esempio:

```powershell
python -m virgilio_connector scan-imap-accounts `
  --config accounts.local.yaml `
  --dry-run
```

Il comando interroga solo gli account abilitati, usa la cartella `input_folder`,
non scarica allegati, non fa ack, non sposta messaggi, non chiama Apps Script e
non scrive Bucoliche. Senza `--dry-run` registra in SQLite i messaggi rilevati
separando lo stato per `account_alias`; gli allegati restano a zero in questa
micro-fase.

Per processare gli allegati ammessi in quarantena locale per account:

```powershell
python -m virgilio_connector process-imap-accounts `
  --config accounts.local.yaml `
  --dry-run
python -m virgilio_connector process-imap-accounts `
  --config accounts.local.yaml
```

Il dry-run non scrive file o SQLite. L'esecuzione reale usa `BODY.PEEK[]`, salva
solo allegati ammessi sotto `.local_data/accounts/<account_alias>/quarantine/`,
calcola SHA-256, esegue lo scanner locale configurato e crea un manifest JSON per
allegato. Non fa staging Drive Desktop, non chiama Apps Script, non scrive
Bucoliche, non invia notifiche e non esegue ack IMAP.

### Storage adapter locale

Configurare nel file account locale una sezione storage, oppure usare le variabili
`VIRGILIO_STORAGE_ADAPTER=local_filesystem` e `VIRGILIO_STORAGE_STAGING_DIR`.
Default prudente: la cartella di destinazione deve gia' esistere.

```yaml
storage:
  adapter: local_filesystem
  staging_dir: C:\Percorso\Virgilio_Staging
  use_account_subfolders: true
  copy_manifest: true
  overwrite: false
  create_staging_dir: false
```

Esecuzione:

```powershell
python -m virgilio_connector stage-ready-attachments `
  --config accounts.local.yaml `
  --dry-run
python -m virgilio_connector stage-ready-attachments `
  --config accounts.local.yaml
```

Lo storage adapter copia solo allegati `ready_for_caronte`, verifica SQLite,
manifest e file in quarantena, usa copia atomica `.uploading`/`.partial`, verifica
SHA-256 post-copia e genera un manifest staged accanto al file. I file restano in
quarantena; non viene fatto ack IMAP, non vengono chiamati Apps Script, Bucoliche,
notifiche o staging Drive Desktop automatico.

### Completamento locale controllato

L'ack IMAP e' disabilitato per default. Abilitarlo solo in una casella di test:

```yaml
ack_enabled: true
ack_strategy: add_done_label_only
done_folder: Virgilio/traghettate
```

La strategia iniziale `add_done_label_only` copia il messaggio nella cartella/label
`done_folder` con IMAP `COPY`. Non rimuove il messaggio dalla cartella input, non
usa `STORE`, `MOVE`, `DELETE` o `EXPUNGE` e non marca il messaggio come letto.

Esecuzione:

```powershell
python -m virgilio_connector complete-staged-messages `
  --config accounts.local.yaml `
  --dry-run
python -m virgilio_connector complete-staged-messages `
  --config accounts.local.yaml
```

Il comando completa solo messaggi con almeno un allegato `staged_storage` e senza
stati bloccanti come `scan_failed`, `rejected_malware`, `staging_failed` o
`staging_conflict`. Genera un report JSON in `.local_data/reports/`. Non chiama
Apps Script, non scrive Bucoliche, non invia notifiche e non cancella messaggi.

### Pipeline locale unica

```powershell
python -m virgilio_connector run-local-pipeline --config accounts.local.yaml --dry-run
python -m virgilio_connector run-local-pipeline --config accounts.local.yaml
```

La pipeline esegue scan, process, storage e completamento riusando i blocchi
esistenti. Con `ack_enabled: false` arriva allo staging/report ma non chiude le
mail. Il report unico viene scritto in `.local_data/reports/pipeline_report_*.json`.
Non chiama Apps Script, Bucoliche o notifiche.

### Doctor locale

Prima di un pilota reale:

```powershell
python -m virgilio_connector doctor --config accounts.local.yaml
```

Il doctor verifica config, variabili ambiente senza stampare segreti, IMAP
read-only, SQLite locale, storage e scanner. Stato globale:

- `READY`: prerequisiti ok;
- `READY_WITH_WARNINGS`: eseguibile ma con avvisi, ad esempio scanner assente;
- `BLOCKED`: correggere errori prima della pipeline.

### Scanner locale opzionale

`VIRGILIO_SCANNER=auto` usa Microsoft Defender quando `MpCmdRun.exe` e'
disponibile. La scansione passa `-DisableRemediation`: il connettore non chiede a
Defender di cancellare o correggere il file. Modalita' disponibili:

- `auto` o `windows_defender`: rileva Microsoft Defender;
- `none`: conserva il file come `quarantined_unverified`;
- `clamav`: interfaccia riservata, adapter non ancora configurato.

Solo un esito pulito e completato produce `ready_for_caronte` e sposta il file in
`quarantine/ready`. Scanner assente, timeout o codice ambiguo producono
`quarantined_unverified`; una minaccia confermata da un adapter produce
`rejected_by_scanner`. Questa fase non chiama comunque Caronte.

### Generazione JSON Caronte in dry-run

Dopo una scansione pulita, il comando seguente genera un JSON standard per ogni
messaggio dell'ultimo run completato:

```powershell
$env:PYTHONPATH='src'
python scripts/generate_caronte_dry_run.py
```

I file vengono scritti in `.local_data/commands/dry-run/`. Il generatore apre
SQLite in sola lettura, include esclusivamente allegati `ready_for_caronte`, valida
ogni payload con il contratto `1.0` e imposta sempre `dry_run: true` e
`user_confirmed_command: false`. Non contiene alcun client HTTP, trasporto verso
Caronte o chiamata Apps Script; percorsi locali e byte degli allegati non entrano
nel JSON.

### Invio HTTP metadata-only a Caronte

Configurare localmente in `.env` l'URL della Web App dedicata al collaudo:

```dotenv
VIRGILIO_CARONTE_DRY_RUN_URL=https://script.google.com/macros/s/DEPLOYMENT_ID/exec
VIRGILIO_CARONTE_TIMEOUT_SECONDS=15
```

L'URL reale non deve essere versionato. Senza questa variabile il client termina
con un messaggio esplicito e non tenta alcuna connessione. Per inviare uno dei JSON:

```powershell
$env:PYTHONPATH='src'
python -m virgilio_connector send-caronte-dry-run `
  --command-file ".local_data\commands\dry-run\COMANDO.json"
```

Il client esegue un solo POST, senza retry, dentro l'envelope
`{"action":"local_imap_dry_run","payload":{...}}`. Prima della rete valida il
contratto, impone `dry_run=true` e blocca ricorsivamente campi con byte, base64 o
percorsi locali. Non aggiorna SQLite e non invia file.

In questa fase il bridge Apps Script non carica su Drive, non scrive Bucoliche,
non invia notifiche e non modifica Gmail. La configurazione dell'accesso alla Web
App e' una responsabilita' di deploy da verificare prima di una chiamata reale.

Il primo test E2E metadata-only e' stato completato il 2026-06-23 con deployment
Apps Script versione 11 e un singolo comando: risposta `ok=true`, un metadato
allegato accettato e liste Drive/Bucoliche vuote. Il rapporto e' in
`../docs/CARONTE_DRY_RUN_E2E_REPORT_2026-06-23.md`. Restano obbligatori i controlli
manuali su Drive, Bucoliche, Gmail e notifiche prima di chiudere il collaudo.

## Staging pilota con Google Drive Desktop

La copia locale verso Drive Desktop e' disabilitata per default. Creare manualmente
una cartella Limbo di test nel filesystem sincronizzato e configurare `.env`:

```dotenv
VIRGILIO_LOCAL_DRIVE_STAGING_ENABLED=true
VIRGILIO_LOCAL_DRIVE_STAGING_DIR=C:\percorso\Drive Desktop\Virgilio Limbo Test
```

Il percorso reale resta esclusivamente in `.env`, gia' ignorato da Git. Prima
eseguire sempre:

```powershell
python -m virgilio_connector stage-ready-files --dry-run
```

Controllare l'elenco JSON e poi, soltanto sul Limbo di test:

```powershell
python -m virgilio_connector stage-ready-files
```

Il comando copia solo file `ready_for_caronte`, verifica nuovamente SHA-256, non
cancella l'originale e crea un manifest accanto alla copia. Verificare manualmente
in Drive Desktop:

- presenza di file e manifest;
- assenza di suffissi `.uploading` o `.partial` dopo un esito positivo;
- completamento della sincronizzazione mostrato dal client;
- nessun file nelle cartelle pratica.

**Lo stato `staged_local_drive` non conferma la sincronizzazione cloud.** Non vengono
usati Drive API, rclone, base64, Caronte, Bucoliche, notifiche o operazioni Gmail.
Dettagli: `../docs/LOCAL_DRIVE_STAGING_TRANSPORT.md`.

## Verifica cloud read-only dello staging

Attendere prima che Drive Desktop mostri la sincronizzazione completata. Configurare
in Apps Script la Script Property `VIRGILIO_DRIVE_STAGING_FOLDER_ID` con l'ID della
sola cartella `Limbo_Test_Local`. Il Local Connector usa lo stesso deployment `/exec`
gia' collaudato, configurato separatamente in `.env`:

```dotenv
VIRGILIO_CARONTE_DRIVE_VERIFY_URL=https://script.google.com/macros/s/.../exec
```

Eseguire una sola verifica indicando il manifest locale:

```powershell
python -m virgilio_connector verify-drive-staging `
  --manifest "C:\percorso\Drive Desktop\Limbo_Test_Local\file.pdf.manifest.json"
```

La CLI legge il manifest locale, invia solo sei campi metadata e stampa la risposta
JSON completa. Apps Script cerca file e manifest per nome, legge la dimensione del
file e il contenuto del solo manifest. Non sposta, copia, cancella o modifica Drive;
non aggiorna SQLite, Bucoliche o Gmail e non invia notifiche.

Dettagli e configurazione: `../docs/DRIVE_STAGING_CLOUD_VERIFY.md`.

### Presa in carico di test

Dopo una verifica `cloud_visible=true`, configurare lo stesso endpoint Web App:

```dotenv
VIRGILIO_CARONTE_INTAKE_TEST_URL=https://script.google.com/macros/s/.../exec
```

Il tab `Staging_Local_Test` deve essere creato una sola volta tramite il setup
Apps Script esplicito descritto in
[`../docs/DRIVE_STAGING_TEST_INTAKE.md`](../docs/DRIVE_STAGING_TEST_INTAKE.md).
Quindi inviare un solo manifest:

```powershell
python -m virgilio_connector intake-drive-staging-test --manifest "G:\...\file.pdf.manifest.json"
```

Controllare la riga nel tab `Staging_Local_Test`. Il comando non invia file o
percorsi locali, non usa Drive API dal connettore, non sposta file e non tocca
Gmail, notifiche o il tab Bucoliche operativo.

Un retry identico può restituire `ok=true`, `already_registered=true` e
`test_row_written=false`: è il comportamento idempotente atteso e indica che la
riga esistente non è stata duplicata. Un errore `ATTACHMENT_SHA256_CONFLICT`
indica invece che lo stesso `attachment_id` è associato a un hash differente.

L'adapter usa TLS, apre esclusivamente la cartella configurata con
`SELECT readonly=True` e acquisisce i messaggi con `UID FETCH (BODY.PEEK[])`, che
non imposta il flag `Seen`. `acknowledge()` e' disabilitato: non vengono eseguiti
`STORE`, `COPY`, `MOVE`, `DELETE` o `EXPUNGE`. Il probe stampa soltanto UID e numero
di allegati, non oggetto, mittente, corpo, password o percorsi completi.

**Avvertenza:** non usare su una casella principale finche' il collaudo controllato
non e' stato completato e registrato nel template
`../docs/LOCAL_IMAP_PROBE_REPORT_TEMPLATE.md`.

## Test pytest

```powershell
python -m pip install -e ".[dev]"
pytest
```

## Prossima micro-fase proposta

Eseguire il probe LC3 su una casella di test, verificare la mappatura della cartella
del provider e consolidare retry e recupero dopo interruzione. L'ack reale resta
escluso fino a una decisione esplicita sulla strategia cartelle/label.
