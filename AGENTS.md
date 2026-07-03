# AGENTS.md - Virgilio

## Missione
Virgilio acquisisce documenti da email, li porta nel Limbo, li mette in Da archiviare,
raccoglie la decisione umana e li archivia nella pratica finale registrando tutto nel Registro.

Riferimento architetturale condiviso: `docs/ARCHITETTURA_UNIFICATA.md`.

## Regole permanenti
- Non modificare `main`.
- Lavorare su `codex/v1.1-development` o su una branch derivata.
- Un task per run, un commit per task.
- Non usare mail, Google o credenziali reali nei test.
- Non inviare byte, base64 o path locali ad Apps Script.
- Non versionare segreti, token, password, `.env`, `.env.*`, `.local_data/`, `.secrets/`, `_staging/` o `.clasprc.json`.
- Non introdurre AI, RAG, Docling, LiteLLM, database remoti, server web o nuove GUI.
- Non riscrivere il form.
- Non sostituire Apps Script con Python.
- Non eseguire `clasp push` salvo task esplicito.
- Se il working tree e` sporco per cause non spiegate, fermarsi.

## Workflow
- Verificare branch e `git status --short` prima di modificare.
- Usare `docs/CODEX_STATE.md` e `docs/NEXT_CODEX_TASKS.md` come fonti operative primarie.
- Usare `docs/DEV_BACKLOG.md` solo per il task selezionato.
- Usare `docs/ARCHITETTURA_UNIFICATA.md` solo per dubbi architetturali.
- Usare `docs/CLASP_WORKFLOW.md` solo per task Apps Script o `clasp`.
- Tenere i cambi piccoli, reversibili e coerenti con il lessico ufficiale.

## Test
- Se si tocca codice, aggiungere test mirati prima dello smoke.
- Quando il task tocca il percorso locale o la governance di sviluppo, eseguire
  `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1`.
- Non usare servizi reali nei test.

## Chiusura run
- Verificare diff, stato git e assenza di segreti.
- Aggiornare `docs/CODEX_STATE.md`, `docs/NEXT_CODEX_TASKS.md` e, se necessario, solo la sezione pertinente di `docs/DEV_BACKLOG.md`.
- Verificare `docs/DEFINITION_OF_DONE.md` prima di chiudere il task.
- Committare solo quando il task e` completo.
- Non fare merge o reset distruttivi.
