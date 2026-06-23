# State database locale

## Scopo

`state.db` conserva lo stato tecnico e recuperabile del Local IMAP Connector. Non sostituisce Bucoliche e non e' un archivio documentale.

Il database serve a:

- riconoscere messaggi IMAP gia' osservati;
- mantenere lo stato degli allegati nella quarantena locale;
- registrare tentativi verso Caronte senza conservare payload completi;
- impedire ack prematuri;
- supportare retry e diagnosi locale.

## Posizione e versionamento

Il percorso viene fornito esplicitamente a `StateStore`. Il nome operativo previsto e' `state.db`, escluso da Git insieme ai file SQLite `-wal` e `-shm`.

Lo schema usa `PRAGMA user_version`. La versione iniziale e' `1`; database creati da versioni future non vengono aperti automaticamente da codice piu' vecchio.

## Tabelle

### `messages`

Identifica un messaggio con la chiave composta:

```text
account_alias + mailbox + mailbox_uidvalidity + message_uid
```

UIDVALIDITY e' obbligatorio nel modello persistente per distinguere UID riutilizzati dal server.

Stati:

```text
discovered -> quarantined -> ready -> submitting -> ack_pending -> acknowledged
```

Sono previsti anche `rejected` ed `error`. Da `error` e' ammesso soltanto il ritorno controllato a `discovered`.

### `attachments`

Conserva metadati, percorso relativo alla radice di quarantena, SHA-256, stato scansione e gli identificativi restituiti da Caronte.

Non conserva i byte del file. `uploaded_to_limbo` richiede un `drive_file_id` non vuoto.

### `command_attempts`

Registra ogni tentativo usando:

- `command_id`;
- numero progressivo del tentativo;
- SHA-256 della richiesta serializzata;
- esito sintetico;
- codice errore e retryability.

Il JSON completo non viene conservato per ridurre dati duplicati e rischio privacy.

### `state_events`

Audit minimo delle transizioni di messaggi e allegati. Registra stato precedente, nuovo stato, motivo e timestamp.

## Sicurezza e privacy

`state.db` non deve contenere:

- password IMAP;
- token OAuth;
- cookie o header di autenticazione;
- byte degli allegati;
- payload completi verso Caronte.

Oggetto e mittente sono presenti per recupero operativo locale. Retention, cifratura disco e minimizzazione restano decisioni da completare prima del pilota.

## Transazioni

Le scritture usano `BEGIN IMMEDIATE`, foreign key abilitate e rollback automatico su errore. SQLite opera in modalita' WAL con timeout configurabile.

La registrazione iniziale e' idempotente sulla chiave IMAP. Un `local_temp_id` gia' associato agli stessi dati viene riusato; un'associazione differente produce conflitto.

## Vincolo ack

Un messaggio non puo' passare ad `acknowledged` se non esiste almeno un allegato:

- nello stato `uploaded_to_limbo`;
- con `drive_file_id` valorizzato.

Questa regola protegge lo stato locale. L'esecuzione IMAP reale dell'ack non e' implementata.

## Migrazioni future

Ogni modifica allo schema dovra':

1. incrementare `DATABASE_SCHEMA_VERSION`;
2. introdurre una migrazione esplicita e testata;
3. eseguire backup prima della migrazione;
4. non effettuare downgrade automatici;
5. mantenere compatibilita' con i dati strettamente necessari al retry.
