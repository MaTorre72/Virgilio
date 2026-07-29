# Documentazione per lo sviluppo

Questa sezione e` destinata a sviluppatori e automazioni. Non serve per usare
Virgilio.

## Da leggere per contribuire

1. `AGENTS.md`: regole permanenti del repository.
2. `docs/DEFINITION_OF_DONE.md`: criteri verificabili di chiusura.
3. [ROADMAP_1_1.md](ROADMAP_1_1.md): lessico, fasi e stato raggiunto.
4. `docs/CODEX_STATE.md`: fotografia operativa corrente.
5. `docs/NEXT_CODEX_TASKS.md`: eventuale task Codex corrente.

## Documenti interni

| File | Scopo |
| --- | --- |
| `DEV_BACKLOG.md` | backlog storico/operativo dello sviluppo |
| `CONSOLIDATION_PROGRAM.md` | programma concluso di pubblicazione e pulizia 1.1 |
| `CHANGELOG_DEV.md` | cronologia tecnica dettagliata |
| `SURFACE_INVENTORY.md` | audit di entry point, packaging e asset |
| `HANDOFF_1_1.md` | evidenze della consegna finale |
| `DOCUMENT_INVENTORY.md` | mappa delle fonti documentali |

Questi file non devono essere citati come manuale utente o come prerequisito
operativo. Il changelog pubblico resta `CHANGELOG.md`.

## Flusso Git

- partire da `main` aggiornato e creare una branch dedicata;
- un task misurabile e un commit atomico;
- usare fixture sintetiche e nessun servizio reale nei test;
- eseguire test mirati e poi lo smoke richiesto;
- verificare diff, segreti e tree prima del push;
- aprire una pull request e lasciare approvazione e merge alla revisione umana.
