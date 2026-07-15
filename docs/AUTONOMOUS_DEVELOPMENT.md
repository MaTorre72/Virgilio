# Sviluppo autonomo

`AGENTS.md` e` la policy permanente. Questo file resta un riferimento esteso e non va letto a ogni run se bastano i file brevi.

## Fonti operative leggere
- `docs/CODEX_STATE.md` per lo stato corrente.
- `docs/NEXT_CODEX_TASKS.md` per il task corrente.

## Consultazione on demand
- `docs/DEV_BACKLOG.md` per il backlog attivo del task scelto.
- `docs/DEV_BACKLOG_ARCHIVE.md` e `docs/CHANGELOG_DEV.md` solo per ricostruzione storica.
- `docs/ARCHITETTURA_UNIFICATA.md` per dubbi architetturali.
- `docs/CLASP_WORKFLOW.md` per task Apps Script o `clasp`.

## Regola operativa
Una run autonoma resta seriale, un task per volta, e si chiude aggiornando
stato, backlog e commit senza sovrapposizioni.

## Toolchain dell'attivita` programmata

- Eseguire `pytest` con `local_connector\.venv\Scripts\python.exe`.
- Non usare `.venv\Scripts\python.exe` nella root: quella venv non contiene `pytest`.
- Lo smoke `scripts\dev\smoke_local_connector.ps1` usa gia` la venv corretta.
