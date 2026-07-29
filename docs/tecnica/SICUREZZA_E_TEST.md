# Sicurezza e test della 1.1

## Principi

Virgilio deve essere tracciabile, idempotente, reversibile, privo di segreti
versionati e capace di fermarsi in sicurezza su errore parziale.

## Controlli implementati

- lettura IMAP senza marcatura involontaria;
- isolamento multi-account e credenziali protette;
- quarantena locale prima del Limbo;
- allowlist dei formati e scanner locale;
- hash SHA-256, identita` stabile e deduplicazione;
- retry limitati durante la sincronizzazione Drive;
- intake metadata-only verso Apps Script;
- Registro append-only e stato tecnico locale;
- ack IMAP soltanto dopo archiviazione e audit riusciti;
- reset con lock e backup verificati.

Macro, archivi compressi, eseguibili e script restano bloccati. I documenti
Office ammessi richiedono scansione. Nessun allegato viene aperto
automaticamente.

## Matrice aggiornata dalla roadmap

| Area | Obiettivo originario | Stato 1.1 |
| --- | --- | --- |
| IMAP read-only / BODY.PEEK | non alterare la mail | completato |
| Multi-account | caselle isolate e errore per account | completato |
| Quarantena e scanner | verificare prima del Limbo | completato |
| SQLite | stato operativo persistente | completato |
| Idempotenza | nessun duplicato su retry | completato |
| Drive Desktop | staging locale e verifica cloud | completato |
| Da archiviare | una coda umana per documento | completato |
| Ack IMAP locale | completare sulla casella di origine | completato |
| Registro | audit unico e leggibile | completato |
| Storage adapter | consegna alla pratica finale | completato |
| Notifier adapter | notifiche non bloccanti | completato |
| Pilota | percorso reale con rollback | PASS umano 2026-07-28 |

La suite offline finale contiene 548 test. I test automatici non usano mail,
Google, credenziali o servizi reali. Build e installer 1.1.0 hanno superato gli
smoke dedicati.

## Rischi residui

- la sincronizzazione Drive non e` istantanea e puo` richiedere retry;
- il completamento Gmail dipende dalle estensioni IMAP del provider;
- reset, deploy e operazioni reali richiedono autorizzazione e backup;
- manutenzione, aggiornamenti e rotazione credenziali restano responsabilita`
  operative locali.
