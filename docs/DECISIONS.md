# Decisioni v1.1

> Documento storico assorbito in
> `docs/ARCHITETTURA_UNIFICATA.md`. Stati e decisioni qui sotto fotografano una
> fase precedente e non sono una fonte corrente.

## Decisioni assunte

| ID | Decisione | Stato |
|---|---|---|
| D01 | Google Workspace resta prototipo/adattatore, non vincolo definitivo | Assunta |
| D02 | Caronte evolve in motore locale provider-agnostico | Assunta |
| D03 | SQLite locale e' il registro operativo primario v1.1 | Assunta |
| D04 | Bucoliche e' output adapter, non database primario | Assunta |
| D05 | Drive Desktop e' adapter iniziale di test, non architettura finale | Assunta |
| D06 | Ack IMAP automatico resta bloccato fino a checkpoint dedicato | Assunta |

## Decisioni aperte

| ID | Tema | Domanda |
|---|---|---|
| A01 | Multi-account | Formato configurazione e isolamento per casella |
| A02 | Ack | Quale evento autorizza davvero ack/spostamento |
| A03 | Storage finale | Cartelle locali, Drive API, Drive Desktop o altro |
| A04 | Bucoliche | Schema minimo dell'output adapter |
| A05 | Pilota | Due utenti, caselle e dataset di prova |

## Branch policy

- Integrare solo branch con test automatici o collaudo documentato.
- Archiviare branch sperimentali superate dopo merge/consolidamento.
- Tenere fuori i rami operativi Google P3/P4 dalla linea Caronte Locale finche' restano dipendenti da Apps Script/GmailApp.
