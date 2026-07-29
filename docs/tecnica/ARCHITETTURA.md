# Architettura tecnica Virgilio 1.1

## Modello

La 1.1 realizza la direzione **local-first** definita dalla roadmap originale:

```text
Utente
  -> client email e cartella da-traghettare
  -> Caronte Locale
      -> lettura IMAP multi-account
      -> quarantena locale e scansione
      -> stato SQLite e idempotenza
      -> Limbo tramite Drive Desktop
  -> Apps Script / adapter Google
      -> Da archiviare
      -> Form Virgilio
      -> pratica finale
      -> Registro e notifiche
  -> ack IMAP sulla casella di origine
```

## Ruoli

| Componente | Responsabilita` |
| --- | --- |
| Virgilio | interfaccia, guida, supervisione e decisione umana |
| Caronte Locale | motore operativo multi-casella e provider-agnostico |
| Caronte | applicazione utente ordinaria |
| Caronte Manutenzione | configurazione tecnica, diagnostica, backup e reset |
| Apps Script | adapter Google per form, Drive, coda e audit |
| SQLite | stato operativo tecnico locale |
| Registro (`bucoliche`) | audit cloud umano append-only |
| Drive Desktop | storage adapter iniziale verso il Limbo |
| Chat / Telegram | notifier adapter opzionali |

La CLI usa gli stessi servizi applicativi delle due GUI. Non e` una terza GUI
e non possiede logica operativa duplicata.

## Flusso del documento

1. L'utente assegna una mail alla cartella configurata.
2. Caronte Locale legge senza modificare il messaggio e identifica gli allegati.
3. Gli allegati ammessi entrano in quarantena, vengono verificati e registrati.
4. File e metadati raggiungono il Limbo; retry e hash impediscono duplicazioni.
5. Apps Script crea una voce in Da archiviare e rende disponibile il form.
6. La decisione umana assegna il documento alla pratica finale.
7. Il Registro riceve l'esito; solo dopo avviene l'ack IMAP.

## Dati e stati

- `attachment_id`, fingerprint e SHA-256 rendono idempotenti acquisizione e retry.
- SQLite conserva stato, follow-up, errori e conflitti tecnici locali.
- `Virgilio_Inbox` e` il nome tecnico della coda **Da archiviare**.
- `bucoliche` e` l'unico Registro cloud attivo.
- Il Limbo non e` l'archivio finale e non sostituisce la quarantena locale.

Stati principali: acquisito, in quarantena, verificato, consegnato al Limbo,
da lavorare, in lavorazione, archiviato e completato. Un errore parziale non
deve produrre un falso completamento.

## Confini

- Nessun byte, base64 o percorso locale viene inviato ad Apps Script.
- Il form resta unico e Apps Script non viene sostituito da Python.
- Le credenziali restano nel deposito protetto locale o nelle proprieta` del
  servizio autorizzato, mai nel repository.
- AI, RAG, Docling, LiteLLM, database remoti e server web non fanno parte della
  1.1.
- Le implementazioni GUI legacy non sono supportate.

Il riferimento storico compatibile resta [ARCHITETTURA_UNIFICATA.md](../ARCHITETTURA_UNIFICATA.md).
