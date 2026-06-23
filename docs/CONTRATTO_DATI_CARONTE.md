# Contratto dati Caronte

## Scopo e stato

Questo documento propone il contratto tra un connettore di ingresso e Caronte. E' una specifica preliminare e non descrive ancora un endpoint implementato.

Il contratto separa:

- acquisizione email e quarantena, responsabilita' del connettore;
- Drive, Limbo Drive, Bucoliche e notifiche, responsabilita' di Caronte.

## Regole generali

- JSON codificato UTF-8.
- Date in formato ISO 8601 con timezone.
- Dimensioni in byte interi non negativi.
- Hash SHA-256 in formato esadecimale minuscolo.
- `local_temp_id` e' un identificativo opaco: non deve contenere un percorso locale.
- Il payload non contiene password, token, cookie o credenziali IMAP.
- `message_uid` e' significativo solo insieme a mailbox e UIDVALIDITY.
- I retry devono riusare `command_id` per permettere idempotenza futura.

## Comando verso Caronte

```json
{
  "schema_version": "1.0",
  "command_id": "01900000-0000-7000-8000-000000000001",
  "created_at": "2026-06-23T10:15:30+02:00",
  "connector_id": "workstation-alias:connector-instance",
  "connector_type": "local_imap",
  "account_alias": "utente-01",
  "provider_hint": "generic_imap",
  "mailbox": "Virgilio/da-traghettare",
  "mailbox_uidvalidity": "123456789",
  "message_uid": "4821",
  "message_id": "<opaque-message-id@example.invalid>",
  "thread_id": null,
  "subject": "Documento di prova",
  "from": "sender@example.invalid",
  "date": "2026-06-23T09:52:00+02:00",
  "user_confirmed_command": true,
  "attachments": [
    {
      "local_temp_id": "att-0001",
      "original_filename": "documento.pdf",
      "sanitized_filename": "documento.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 245760,
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "quarantine_status": "ready_for_caronte",
      "scan_engine": "none",
      "scan_result": "not_scanned"
    }
  ],
  "requested_action": "stage_attachments_in_limbo",
  "dry_run": true
}
```

### Campi del comando

| Campo | Obbligatorio | Descrizione |
|---|---|---|
| `schema_version` | Si | Versione del contratto |
| `command_id` | Si | Identificativo idempotente del comando |
| `created_at` | Si | Data di creazione del comando |
| `connector_id` | Si | Istanza logica del connettore, non segreta |
| `connector_type` | Si | Valore fisso `local_imap` |
| `account_alias` | Si | Alias locale, non credenziale e non necessariamente email |
| `provider_hint` | Si | Indicazione non vincolante del provider |
| `mailbox` | Si | Cartella convenzionale letta |
| `mailbox_uidvalidity` | Raccomandato | Protegge dal riuso degli UID IMAP |
| `message_uid` | Si | UID IMAP nel contesto della mailbox |
| `message_id` | Si | Header Message-ID, se disponibile; altrimenti stringa vuota |
| `thread_id` | No | ID conversazione se fornito dal provider |
| `subject` | Si | Oggetto email, con limite da definire |
| `from` | Si | Mittente; minimizzazione e retention sono DA DECIDERE |
| `date` | Si | Data dichiarata del messaggio |
| `user_confirmed_command` | Si | Deve essere `true` per richieste operative |
| `attachments` | Si | Lista, anche vuota in `dry_run` |
| `requested_action` | Si | Inizialmente `stage_attachments_in_limbo` |
| `dry_run` | Si | Se `true`, Caronte non deve produrre effetti persistenti |

### Vincoli sugli allegati

- Solo allegati con `quarantine_status = ready_for_caronte` possono essere accettati in modalita' operativa.
- `sha256` identifica il contenuto e non sostituisce un controllo antivirus.
- `mime_type` dichiarato dall'email non deve essere considerato prova sufficiente del formato reale.
- Il meccanismo di trasferimento dei byte non e' definito da questo JSON. `local_temp_id` consente di correlare metadati e contenuto nel trasporto futuro.

## Risposta standard di Caronte

```json
{
  "schema_version": "1.0",
  "command_id": "01900000-0000-7000-8000-000000000001",
  "ok": true,
  "accepted_attachments": [
    {
      "local_temp_id": "att-0001",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ],
  "rejected_attachments": [],
  "limbo_drive_ids": [
    {
      "local_temp_id": "att-0001",
      "drive_file_id": "opaque-drive-id"
    }
  ],
  "bucoliche_rows": [
    {
      "local_temp_id": "att-0001",
      "row_reference": "opaque-row-reference"
    }
  ],
  "message": "Un allegato acquisito nel Limbo Drive.",
  "errors": []
}
```

### Campi della risposta

| Campo | Descrizione |
|---|---|
| `ok` | Esito complessivo del comando |
| `accepted_attachments` | Allegati accettati da Caronte |
| `rejected_attachments` | Allegati rifiutati, con codice e motivo futuri |
| `limbo_drive_ids` | Correlazione tra allegato locale e file Drive |
| `bucoliche_rows` | Riferimenti opachi alle registrazioni effettuate |
| `message` | Messaggio sintetico per log locale |
| `errors` | Errori strutturati, anche in caso di successo parziale |

## Regola di ack

Il connettore puo' eseguire l'ack IMAP soltanto quando sono vere tutte le condizioni:

1. `dry_run` era `false`;
2. `ok` e' `true`;
3. `accepted_attachments` contiene almeno un elemento;
4. ogni allegato considerato accettato ha un corrispondente `drive_file_id` non vuoto;
5. `command_id` della risposta coincide con quello inviato.

La presenza di una riga Bucoliche e' utile per audit, ma il comportamento in caso di registrazione fallita dopo upload Drive e' **DA DECIDERE**. Il connettore non deve tentare di correggere direttamente Drive o Sheets.

## Errori e successo parziale

Forma proposta per un errore:

```json
{
  "code": "ATTACHMENT_REJECTED",
  "local_temp_id": "att-0002",
  "message": "Tipo di file non ammesso.",
  "retryable": false
}
```

Un successo parziale puo' avere `ok: true`, allegati sia accettati sia rifiutati e una lista `errors`. L'ack della mail intera in questo caso e' **DA DECIDERE**: le opzioni sono ack con log dei rifiuti, stato errore, oppure ack per-allegato non rappresentabile direttamente in IMAP.

## Privacy e logging

- Non loggare il contenuto degli allegati.
- Non loggare credenziali o header di autenticazione.
- Valutare se `from` e `subject` debbano essere minimizzati nei log locali.
- Usare `command_id`, `local_temp_id` e hash per correlazione tecnica.
- Definire retention dei log prima del pilota.
