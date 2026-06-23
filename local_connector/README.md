# Virgilio Local Connector

Skeleton Python del connettore locale di ingresso per Virgilio.

## Stato

Il package contiene esclusivamente logica locale e astratta:

- modelli immutabili del contratto JSON con Caronte;
- parsing e serializzazione JSON;
- regola prudenziale per autorizzare un futuro ack;
- sanitizzazione dei nomi e calcolo SHA-256;
- policy iniziale sulle estensioni;
- macchina a stati della quarantena;
- porte astratte per mailbox, antivirus e Caronte;
- test automatici senza rete.

**Non contiene una connessione IMAP reale, chiamate HTTP, esecuzione antivirus o credenziali.**

## Confini

Il connettore locale potra' occuparsi soltanto di:

- lettura IMAP limitata alla cartella configurata;
- download degli allegati selezionati dall'utente;
- quarantena e filtri locali;
- adapter per eventuale antivirus locale;
- costruzione del comando verso Caronte;
- ack della mail dopo conferma valida.

Restano in Apps Script:

- Drive e Limbo Drive;
- Bucoliche;
- notifiche;
- apertura e gestione delle pratiche;
- nucleo operativo Caronte.

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
  tests/
    fixtures.py
    test_ack.py
    test_contract.py
    test_files_policy.py
    test_no_network.py
    test_quarantine.py
```

## Test

Da `local_connector/`, con Python 3.11 o successivo:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -p 'test_*.py' -v
```

Non e' necessario installare dipendenze esterne.

## Documentazione

- [`../docs/LOCAL_IMAP_CONNECTOR.md`](../docs/LOCAL_IMAP_CONNECTOR.md)
- [`../docs/CONTRATTO_DATI_CARONTE.md`](../docs/CONTRATTO_DATI_CARONTE.md)
- [`../docs/QUARANTENA_LOCALE.md`](../docs/QUARANTENA_LOCALE.md)

## Credenziali

Non creare file di credenziali nel repository. La strategia futura per password applicative, OAuth2 o keyring locale resta da decidere.

## Prossima micro-fase proposta

Creare adapter finti in memoria per simulare l'orchestrazione completa senza rete:

1. messaggio sintetico in ingresso;
2. allegati fittizi in una directory temporanea;
3. scanner finto configurabile;
4. Caronte finto con successo ed errori;
5. prova che l'ack astratto avvenga solo dopo conferma valida.

La connessione IMAP reale resta esclusa dalla prossima micro-fase.
