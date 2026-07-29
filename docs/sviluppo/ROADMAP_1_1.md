# Roadmap Virgilio 1.1

Questa roadmap aggiorna il documento local-first originario usando lo stesso
lessico. Le fasi A-H non sono piu` intenzioni: descrivono il percorso completato
che ha portato alla release ufficiale 1.1.0.

## Direzione architetturale

```text
Virgilio = interfaccia, guida, supervisione
Caronte Locale = motore operativo locale multi-casella
Apps Script = adapter Google
SQLite = stato tecnico locale
Bucoliche / Registro = audit cloud umano
```

## Stato delle fasi

| Fase | Obiettivo originario | Risultato raggiunto | Stato |
| --- | --- | --- | --- |
| A - Consolidamento | ridurre rami, duplicati e ambiguita` | release 1.1.0, documentazione canonica, repository pulito | completata |
| B - Multi-account IMAP locale | caselle isolate e provider-agnostiche | configurazione multi-account, errori isolati, OAuth Gmail | completata |
| C - Quarantena e staging per account | evitare commistioni e duplicati | identita` per account, hash, quarantena, Limbo piatto e idempotenza | completata |
| D - Ack IMAP locale | chiudere sulla casella di origine | copia etichetta finale, rimozione etichetta ingresso e post-condizione verificata | completata |
| E - SQLite e Bucoliche adapter | stato persistente e audit ispezionabile | stato tecnico locale e unico Registro cloud append-only | completata |
| F - Storage adapter | consegna configurabile | Drive Desktop verso Limbo e Apps Script verso pratica finale | completata |
| G - Notifiche adapter | notifiche non bloccanti | Google Chat e Telegram separati dallo stato primario | completata |
| H - Pilota | flusso reale con rollback | reset con backup e collaudo umano PASS del 28 luglio 2026 | completata |

## Decisioni consolidate

- Il multi-casella non usa GmailApp come motore principale.
- Il gesto intenzionale dell'utente resta l'ingresso del flusso.
- Il Limbo e` distinto dalla quarantena e dalla pratica finale.
- SQLite conserva lo stato tecnico; il Registro conserva l'audit umano.
- L'ack avviene solo dopo archiviazione e audit riusciti.
- Apps Script resta l'adapter Google e il form non viene riscritto.
- AI e database remoti restano fuori dalla 1.1.

## Oltre la 1.1

Le evoluzioni future devono essere aperte come nuovi programmi, non come
rifiniture indefinite della 1.1:

1. semplificare ulteriormente installazione e aggiornamento su piu` postazioni;
2. estendere la compatibilita` IMAP mantenendo post-condizioni verificabili;
3. migliorare osservabilita`, backup e recupero senza esporre dettagli tecnici
   nella GUI utente;
4. valutare nuovi storage o notifier adapter solo con un caso d'uso concreto;
5. mantenere AI, servizi remoti e nuovi database fuori dal nucleo finche` non
   esistono requisiti, governance e test dedicati.
