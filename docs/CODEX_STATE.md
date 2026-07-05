# Codex State

- Branch attesa: `codex/v1.1-development`
- Modalita: run autonoma/oraria, seriale, un task per run
- Milestone attiva: `v1.1.3 - Virgilio unificato`
- Task 0.0: chiuso
- Ultimo task chiuso noto: `V113-E6-T04 - Nascondere dettagli macchina nella UX normale`
- Task corrente consigliato: nessuno noto
- Massimo due successivi: nessuno noto
- Blocchi aperti: backlog v1.1.3 esaurito; nessun TODO eleggibile nella sezione pertinente di `docs/DEV_BACKLOG.md`
- Ultimo report test: `docs/TEST_REPORT_20260704.md` -> `PASS_WITH_WARNINGS`; blocchi pratici: install editable offline non autosufficiente, mentre i collaudi reali sul mailbox di test e l'idempotenza sono stati confermati
- Ultima readiness test: `docs/TEST_READINESS_20260704.md`; documentazione riallineata sul runtime `local_connector\.venv\Scripts\python.exe`, toolchain locale `node/npm/clasp` verificata via percorsi completi, `clasp status` confermato, collaudi Bucoliche e run reale del pilot confermati; resta solo il limite packaging offline
- Ultima readiness GAS: `docs/GAS_PUSH_REPORT_20260705.md` -> `GO`; mirror `apps_script/src` -> `apps_script/clasp` riallineato, `clasp push -f` completato e distribuzione `@28` pubblicata sulla v1.1.3
- Ultima verifica configurazione: `docs/CONFIG_ALIGNMENT_VIRGILIO_V1_1.md` -> `PRONTO_CON_RISERVE`; nomi e contratti allineati, con sola conferma live residua per Script Properties e ID Google
- Ultima normalizzazione config: `apps_script/src/caronte.gs`, `apps_script/src/virgilio_inbox.gs`, `apps_script/src/setup.gs`, `apps_script/src/test.gs` e `local_connector/.env.example` parlano ora la stessa lingua sugli ID operativi; live GAS non ancora ripubblicato in questa run
- Archivio GAS: `apps_script/archive/pre_push_gas_20260704_114328/`; snapshot del mirror precedente preservato prima della sync
- Policy permanente: `AGENTS.md`
- Leggere sempre: `docs/CODEX_STATE.md`, `docs/NEXT_CODEX_TASKS.md`, `docs/DEFINITION_OF_DONE.md`
- Leggere on demand: `docs/DEV_BACKLOG.md`, `docs/DEV_BACKLOG_ARCHIVE.md`, `docs/CHANGELOG_DEV.md`, `docs/ARCHITETTURA_UNIFICATA.md`, `docs/CLASP_WORKFLOW.md`
- Fine run: aggiornare questo file solo se cambia il task corrente o uno dei blocchi
