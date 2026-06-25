# Caronte Locale

Caronte Locale e' la direzione v1.1: un motore operativo locale che riceve eventi da una o piu' caselle e decide azioni controllate tramite adapter.

## Responsabilita'

- leggere input normalizzati dal Local IMAP Connector;
- mantenere stato operativo in SQLite;
- applicare policy allegati;
- coordinare quarantena, scansione e preparazione all'azione;
- invocare adapter opzionali solo quando configurati.

## Adapter previsti

| Adapter | Stato |
|---|---|
| IMAP read-only | implementato in forma sperimentale |
| Quarantena locale | implementata |
| Scanner locale | opzionale, Windows Defender iniziale |
| JSON Caronte dry-run | implementato |
| Apps Script dry-run | sperimentale metadata-only |
| Drive Desktop staging | sperimentale |
| Bucoliche output | da isolare come adapter |

## Regole di sicurezza

- niente credenziali nel codice;
- niente byte/base64 nei payload metadata-only;
- niente percorsi locali verso servizi remoti;
- niente ack prima di stato locale e output coerenti;
- niente modifica IMAP nei flussi read-only.

## Direzione

Il prossimo passo tecnico non e' aggiungere feature, ma rendere esplicito il modello multi-account e il ciclo ack locale.
