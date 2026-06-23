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
