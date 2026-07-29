# Mappa delle fonti documentali

L'ingresso unico e` [README.md](README.md). Da qui la documentazione si divide
in tre aree senza sovrapposizioni.

| Area | Fonti correnti | Pubblico |
| --- | --- | --- |
| Utente | `docs/utente/MANUALE.md` | utilizzatori di Caronte e Virgilio |
| Tecnica | `docs/tecnica/ARCHITETTURA.md`, `INSTALLAZIONE_E_COMANDI.md`, `SICUREZZA_E_TEST.md` | amministratori e sviluppatori |
| Sviluppo | `docs/sviluppo/README.md`, `ROADMAP_1_1.md` e i documenti Codex elencati sotto | manutentori e automazioni |

`docs/ARCHITETTURA_UNIFICATA.md` e `docs/RUNBOOKS.md` sono soltanto puntatori
di compatibilita` verso la nuova documentazione tecnica.

## Documenti interni di sviluppo

- `CODEX_STATE.md`, `NEXT_CODEX_TASKS.md` e `DEV_BACKLOG.md`: stato e lavoro;
- `CONSOLIDATION_PROGRAM.md` e `HANDOFF_1_1.md`: programma e consegna 1.1;
- `CHANGELOG_DEV.md`: cronologia tecnica;
- `SURFACE_INVENTORY.md`: audit delle superfici;
- `DEFINITION_OF_DONE.md`: governance dei task;
- `.github/codex/prompts/*.md`: ingressi specializzati Codex;
- `local_connector/tests/README.md`: organizzazione della suite.

Questi file non sono manuali utente e non definiscono prerequisiti operativi.
La storia pubblica delle versioni resta in `CHANGELOG.md`.
