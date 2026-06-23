# Virgilio Local Connector

Skeleton Python del connettore locale di ingresso per Virgilio.

## Stato

Il package contiene esclusivamente logica locale e astratta:

- modelli immutabili del contratto JSON con Caronte;
- parsing e serializzazione JSON;
- regola prudenziale per autorizzare un futuro ack;
- sanitizzazione nomi, SHA-256 e policy estensioni;
- macchina a stati della quarantena;
- porte astratte per mailbox, antivirus e Caronte;
- persistenza tecnica SQLite in `state.db`;
- test automatici senza rete.

**Non contiene una connessione IMAP reale, chiamate HTTP, esecuzione antivirus o credenziali.**

## Confini

Il connettore locale potra' occuparsi soltanto di lettura IMAP limitata, download nella quarantena, filtri locali, costruzione del comando e ack dopo conferma valida.

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

## Prossima micro-fase proposta

Creare adapter finti in memoria per simulare l'orchestrazione completa senza rete. La connessione IMAP reale resta esclusa dalla prossima micro-fase.
