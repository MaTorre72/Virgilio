# Virgilio

Virgilio e' il progetto interno Sigma+ per guidare apertura pratiche, presa in carico allegati e tracciamento operativo.

Il progetto nasce come MVP Google Workspace mono-utente, ma la direzione v1.1 e' ora piu' chiara: evolvere verso **Caronte Locale**, un motore operativo locale, multi-casella e meno dipendente da Google Workspace.

## Stato attuale

### v1.0 - MVP Google Workspace mono-utente

La v1.0 usa Google Apps Script, Google Drive, Google Sheets, Gmail, Google Chat e Telegram.

Ha validato il flusso di base:

1. il tecnico compila un form o marca una email da lavorare;
2. Apps Script esegue la logica Caronte;
3. gli allegati vengono depositati nel Limbo;
4. le operazioni vengono registrate in Bucoliche;
5. il team riceve una notifica.

La v1.0 resta utile come prototipo funzionante, ma non risolve il multi-casella: `GmailApp` opera solo sulla casella dell'account che esegue lo script.

### v1.1 - Evoluzione verso Caronte Locale

La v1.1 sposta il baricentro verso un nucleo locale:

- **Virgilio**: interfaccia, guida e supervisione umana;
- **Caronte Locale**: motore operativo locale, multi-casella e provider-agnostico;
- **Apps Script**: adapter Google opzionale;
- **SQLite locale**: registro operativo primario;
- **Bucoliche**: output adapter ispezionabile, non database definitivo;
- **Drive Desktop / filesystem**: storage adapter iniziale, non architettura definitiva.

## Sviluppi gia' completati nella linea locale

Sono stati sviluppati e testati i seguenti blocchi:

- lettura IMAP read-only;
- uso di `BODY.PEEK` senza marcare automaticamente le mail come lette;
- quarantena/staging locale degli allegati;
- scansione locale opzionale;
- manifest JSON per allegato;
- SQLite locale per stato e tracciamento;
- staging verso cartella locale sincronizzata con Drive Desktop;
- verifica cloud read-only tramite Apps Script;
- intake test su tab `Staging_Local_Test`;
- P4 chiuso solo sul contesto Gmail visto da Apps Script/GmailApp.

Questi sviluppi non vanno buttati: vanno ricondotti dentro la linea v1.1 come laboratorio e base tecnica di Caronte Locale.

## Punto chiave emerso

Il test P4 ha confermato il limite strutturale di Apps Script/GmailApp: lo script vede solo la casella dell'account esecutore. Per questo, il multi-casella reale non puo' dipendere da GmailApp come nucleo.

La direzione corretta e':

```text
Caronte Locale legge N caselle IMAP
  -> gestisce quarantena e scansione
  -> registra stato locale
  -> archivia tramite storage adapter
  -> invia notifiche tramite adapter
  -> esegue ack IMAP sulla casella di origine
```

Apps Script resta utile per compatibilita' Google, ma non e' piu' il centro dell'architettura futura.

## Prossime priorita'

1. Consolidare su `codex/v1.1-development` solo il codice stabile.
2. Implementare configurazione multi-account IMAP.
3. Eseguire scan read-only su due caselle.
4. Implementare ack IMAP locale sulla casella di origine.
5. Consolidare SQLite come registro primario.
6. Rendere Bucoliche un adapter opzionale.
7. Preparare storage adapter per cartelle pratica.
8. Fare pilota con due utenti/caselle e dati non critici.

## Documentazione

- [Architettura e roadmap](docs/01_ARCHITETTURA_E_ROADMAP.md)
- [Decisioni e rischi](docs/02_DECISIONI_E_RISCHI.md)
- [Sicurezza e test](docs/03_SICUREZZA_E_TEST.md)
- [Ricognizione e connettori](docs/04_RICOGNIZIONE_E_CONNETTORI.md)
- [Workflow Git](docs/GIT_WORKFLOW.md)
- [Struttura repository](docs/REPO_STRUCTURE.md)

## Principio operativo

**L'AI propone. Il tecnico valida. Il sistema registra.**

Nessuna automazione critica deve archiviare, notificare, spostare o chiudere una mail senza stato tracciabile, idempotenza e possibilita' di verifica o rollback.
