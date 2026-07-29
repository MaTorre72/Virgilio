# Virgilio 1.1

Virgilio acquisisce documenti dalle email, li porta nel **Limbo**, li presenta
in **Da archiviare**, raccoglie la decisione umana e li archivia nella pratica
finale registrando ogni passaggio nel **Registro**.

La versione ufficiale corrente e` **1.1.0**. La versione 1.0 resta disponibile
come rilascio storico nel tag `v1.0`.

## Documentazione

La documentazione e` separata per pubblico. L'indice completo e` in
[docs/README.md](docs/README.md).

- [Manuale utente](docs/utente/MANUALE.md): uso quotidiano di Caronte e
  Caronte Manutenzione.
- [Documentazione tecnica](docs/tecnica/ARCHITETTURA.md): architettura,
  componenti, requisiti e confini.
- [Installazione e comandi](docs/tecnica/INSTALLAZIONE_E_COMANDI.md): setup,
  dipendenze, test, build e manutenzione.
- [Roadmap 1.1](docs/sviluppo/ROADMAP_1_1.md): obiettivi originari, stato
  raggiunto e sviluppi successivi.
- [Documentazione di sviluppo](docs/sviluppo/README.md): file Codex, backlog,
  evidenze e regole per contribuire.

## Architettura in una frase

```text
Virgilio = interfaccia, guida e supervisione
Caronte Locale = motore operativo locale multi-casella
Apps Script = adapter Google per form, Drive, Da archiviare e Registro
```

## Componenti supportati

| Componente | Ruolo |
| --- | --- |
| Caronte | applicazione utente per controllo e attivita` |
| Caronte Manutenzione | configurazione tecnica, diagnostica, backup e reset |
| Caronte Locale | acquisizione IMAP, quarantena, scansione, stato e consegna |
| Apps Script | adapter Google canonico |
| Limbo | cartella condivisa dei documenti acquisiti non ancora archiviati |
| Da archiviare | coda operativa umana |
| Registro | audit append-only degli eventi rilevanti |

Le credenziali, le configurazioni reali e i dati locali non sono versionati.
Test e sviluppo usano esclusivamente fixture sintetiche e servizi simulati.
