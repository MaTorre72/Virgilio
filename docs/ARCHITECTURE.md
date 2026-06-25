# Architettura v1.1

## Visione

Virgilio deve separare guida utente, motore operativo e adattatori esterni.

| Componente | Ruolo v1.1 |
|---|---|
| Virgilio | Interfaccia, guida e supervisione umana |
| Caronte Locale | Motore operativo locale multi-casella |
| Apps Script | Adattatore Google opzionale |
| SQLite locale | Registro operativo primario |
| Bucoliche | Output adapter, non database primario |
| Drive Desktop | Storage adapter iniziale di test |

## Flusso target sintetico

```text
Mailbox / input provider
  -> Local IMAP Connector
  -> quarantena locale
  -> scanner locale opzionale
  -> registro SQLite
  -> Caronte Locale
  -> adapter opzionali: Bucoliche, Drive, notifiche
```

## Principi

- Provider-agnosticita': Gmail non deve essere il vincolo architetturale.
- Registro locale prima degli output esterni.
- Apps Script resta utile per Google Workspace, ma non e' il cuore del sistema.
- Ogni effetto operativo richiede stato locale coerente e auditabile.
- Drive Desktop e' solo un ponte di test, non la soluzione definitiva.

## Fuori perimetro immediato

- AI operativa;
- GUI nuova;
- servizio Windows;
- upload definitivo;
- multi-tenant;
- automazioni irreversibili senza conferma.
