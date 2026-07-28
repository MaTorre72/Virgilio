# Inventario documentale

Inventario completo dei 44 documenti correnti, riallineato da `CONS-D04`
(2026-07-28). I fascicoli ritirati sono elencati dopo la tabella e restano
recuperabili da Git.
Le classi hanno questo significato:

- `KEEP`: documento corrente con responsabilita` distinta;
- `MERGE`: contenuto da assorbire nella destinazione indicata;
- `HISTORY`: evidenza storica, non fonte operativa corrente;
- `REMOVE`: documento eliminabile per la motivazione indicata, recuperabile da Git.

I file sotto `docs/archive/` sono intenzionalmente separati dalle fonti
operative correnti.

| Documento | Classe | Destinazione o motivazione |
| --- | --- | --- |
| `.github/codex/prompts/advance.md` | `KEEP` | prompt operativo distinto |
| `.github/codex/prompts/fix-ci.md` | `KEEP` | prompt operativo distinto |
| `.github/codex/prompts/pilot-hardening.md` | `KEEP` | prompt operativo distinto |
| `.github/codex/prompts/review.md` | `KEEP` | prompt operativo distinto |
| `AGENTS.md` | `KEEP` | regole vincolanti del repository |
| `CHANGELOG.md` | `KEEP` | changelog pubblico della release |
| `README.md` | `KEEP` | ingresso pubblico al progetto |
| `docs/ARCHITECTURE.md` | `MERGE` | assorbire in `docs/ARCHITETTURA_UNIFICATA.md` |
| `docs/ARCHITETTURA_UNIFICATA.md` | `KEEP` | architettura canonica corrente |
| `docs/BUCOLICHE_CONFLICT_POLICY.md` | `KEEP` | policy operativa distinta |
| `docs/BUILD_CARONTE.md` | `KEEP` | runbook build distinto |
| `docs/CHANGELOG_DEV.md` | `HISTORY` | registro cronologico di sviluppo |
| `docs/CLASP_WORKFLOW.md` | `KEEP` | runbook Apps Script distinto |
| `docs/CODEX_STATE.md` | `KEEP` | puntatore operativo corrente |
| `docs/CONSOLIDATION_PROGRAM.md` | `KEEP` | programma operativo corrente CONS |
| `docs/DECISIONS.md` | `MERGE` | assorbire le decisioni correnti in `docs/ARCHITETTURA_UNIFICATA.md` |
| `docs/DEFINITION_OF_DONE.md` | `KEEP` | governance verificabile dei task |
| `docs/DEV_BACKLOG.md` | `KEEP` | backlog operativo corrente |
| `docs/DOCUMENT_INVENTORY.md` | `KEEP` | inventario canonico della classificazione documentale |
| `docs/GOOGLE_OAUTH_DESKTOP.md` | `KEEP` | runbook OAuth Desktop distinto |
| `docs/GUI_UX_REQUIREMENTS.md` | `MERGE` | assorbire i requisiti correnti nell'architettura GUI durante `CONS-D02` |
| `docs/GUI_U_ARCHITETTURA.md` | `MERGE` | assorbire in `docs/ARCHITETTURA_UNIFICATA.md` durante `CONS-D02` |
| `docs/NEXT_CODEX_TASKS.md` | `KEEP` | scheda del task corrente e successore |
| `docs/PARSER_SPIKE_DOCLING_UNSTRUCTURED.md` | `REMOVE` | spike AI vietato dalle regole correnti; recuperabile da Git |
| `docs/RUNBOOKS.md` | `KEEP` | ingresso canonico breve per setup, sviluppo, test, operazioni e release |
| `docs/SETUP_AND_TEST.md` | `KEEP` | runbook setup e test corrente |
| `docs/archive/01_ARCHITETTURA_E_ROADMAP.md` | `HISTORY` | archivio esplicito |
| `docs/archive/02_DECISIONI_E_RISCHI.md` | `HISTORY` | archivio esplicito |
| `docs/archive/03_SICUREZZA_E_TEST.md` | `HISTORY` | archivio esplicito |
| `docs/archive/04_RICOGNIZIONE_E_CONNETTORI.md` | `HISTORY` | archivio esplicito |
| `docs/archive/CARONTE_DRY_RUN_BRIDGE.md` | `HISTORY` | archivio esplicito |
| `docs/archive/CARONTE_DRY_RUN_E2E_REPORT_2026-06-23.md` | `HISTORY` | archivio e rapporto datato |
| `docs/archive/CONTRATTO_DATI_CARONTE.md` | `HISTORY` | contratto storico archiviato |
| `docs/archive/DRIVE_STAGING_CLOUD_VERIFY.md` | `HISTORY` | procedura pilota archiviata |
| `docs/archive/DRIVE_STAGING_TEST_INTAKE.md` | `HISTORY` | procedura pilota archiviata |
| `docs/archive/GIT_WORKFLOW.md` | `HISTORY` | workflow precedente archiviato |
| `docs/archive/LOCAL_DRIVE_STAGING_TRANSPORT.md` | `HISTORY` | trasporto pilota archiviato |
| `docs/archive/LOCAL_IMAP_CONNECTOR.md` | `HISTORY` | specifica precedente archiviata |
| `docs/archive/LOCAL_IMAP_PROBE_REPORT_2026-06-23.md` | `HISTORY` | rapporto datato archiviato |
| `docs/archive/LOCAL_IMAP_PROBE_REPORT_TEMPLATE.md` | `HISTORY` | template del rapporto storico |
| `docs/archive/QUARANTENA_LOCALE.md` | `HISTORY` | specifica precedente archiviata |
| `docs/archive/REPO_STRUCTURE.md` | `HISTORY` | struttura precedente archiviata |
| `docs/archive/STATE_DB.md` | `HISTORY` | specifica precedente archiviata |
| `local_connector/tests/README.md` | `KEEP` | guida distinta alla suite locale |

## Fascicoli ritirati dal percorso corrente

`CONS-D04` ha ritirato 17 backlog, roadmap, report e guide assorbite. Gli esiti
e la baseline 1.1 restano in `CHANGELOG.md`, mentre il dettaglio cronologico
resta in `docs/CHANGELOG_DEV.md`. Ogni file e` recuperabile con
`git show 45a19f4:<percorso>`:

- `docs/AUTONOMOUS_DEVELOPMENT.md`, `docs/LOCAL_CARONTE.md` e
  `local_connector/README.md`;
- `docs/DEV_BACKLOG_ARCHIVE.md`, `docs/GUI_U_BACKLOG.md`,
  `docs/GUI_U_CODE_MAP.md` e `docs/GUI_U_HUMAN_ACCEPTANCE.md`;
- `docs/ROADMAP_V1_1.md`, `docs/VIRGILIO_V112_INTEGRATION_ROADMAP.md` e
  `docs/VIRGILIO_V112_OPEN_QUESTIONS.md`;
- `docs/CONFIG_ALIGNMENT_VIRGILIO_V1_1.md`, i quattro report `GAS_*_20260704.md`
  o `GAS_PUSH_REPORT_20260705.md`, e i due report `TEST_*_20260704.md`.
