# Inventario documentale

Inventario completo dei 61 documenti versionati, riallineato da `CONS-D03`
(2026-07-28).
Le classi hanno questo significato:

- `KEEP`: documento corrente con responsabilita` distinta;
- `MERGE`: contenuto da assorbire nella destinazione indicata;
- `HISTORY`: evidenza storica, non fonte operativa corrente;
- `REMOVE`: documento eliminabile per la motivazione indicata, recuperabile da Git.

La classificazione non esegue fusioni o rimozioni. I file sotto `docs/archive/` e i
report datati sono intenzionalmente separati dalle fonti operative correnti.

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
| `docs/AUTONOMOUS_DEVELOPMENT.md` | `HISTORY` | assorbito in `docs/RUNBOOKS.md` da `CONS-D03` |
| `docs/BUCOLICHE_CONFLICT_POLICY.md` | `KEEP` | policy operativa distinta |
| `docs/BUILD_CARONTE.md` | `KEEP` | runbook build distinto |
| `docs/CHANGELOG_DEV.md` | `HISTORY` | registro cronologico di sviluppo |
| `docs/CLASP_WORKFLOW.md` | `KEEP` | runbook Apps Script distinto |
| `docs/CODEX_STATE.md` | `KEEP` | puntatore operativo corrente |
| `docs/CONFIG_ALIGNMENT_VIRGILIO_V1_1.md` | `HISTORY` | snapshot datato di allineamento 1.1 |
| `docs/CONSOLIDATION_PROGRAM.md` | `KEEP` | programma operativo corrente CONS |
| `docs/DECISIONS.md` | `MERGE` | assorbire le decisioni correnti in `docs/ARCHITETTURA_UNIFICATA.md` |
| `docs/DEFINITION_OF_DONE.md` | `KEEP` | governance verificabile dei task |
| `docs/DEV_BACKLOG.md` | `KEEP` | backlog operativo corrente |
| `docs/DEV_BACKLOG_ARCHIVE.md` | `HISTORY` | backlog chiuso e recuperabile |
| `docs/DOCUMENT_INVENTORY.md` | `KEEP` | inventario canonico della classificazione documentale |
| `docs/GAS_PUSH_REPORT_20260704.md` | `HISTORY` | evidenza datata di pubblicazione GAS |
| `docs/GAS_PUSH_REPORT_20260705.md` | `HISTORY` | evidenza datata di pubblicazione GAS |
| `docs/GAS_READINESS_20260704.md` | `HISTORY` | snapshot datato pre-pubblicazione |
| `docs/GAS_V113_EVIDENCE_MATRIX_20260704.md` | `HISTORY` | matrice di evidenza datata |
| `docs/GOOGLE_OAUTH_DESKTOP.md` | `KEEP` | runbook OAuth Desktop distinto |
| `docs/GUI_UX_REQUIREMENTS.md` | `MERGE` | assorbire i requisiti correnti nell'architettura GUI durante `CONS-D02` |
| `docs/GUI_U_ARCHITETTURA.md` | `MERGE` | assorbire in `docs/ARCHITETTURA_UNIFICATA.md` durante `CONS-D02` |
| `docs/GUI_U_BACKLOG.md` | `HISTORY` | fascicolo completo dell'iniziativa GUI-U chiusa |
| `docs/GUI_U_CODE_MAP.md` | `HISTORY` | mappa di implementazione della baseline GUI-U |
| `docs/GUI_U_HUMAN_ACCEPTANCE.md` | `HISTORY` | evidenza del collaudo umano chiuso |
| `docs/LOCAL_CARONTE.md` | `HISTORY` | assorbito in `docs/RUNBOOKS.md` e nell'architettura canonica da `CONS-D03` |
| `docs/NEXT_CODEX_TASKS.md` | `KEEP` | scheda del task corrente e successore |
| `docs/PARSER_SPIKE_DOCLING_UNSTRUCTURED.md` | `REMOVE` | spike AI vietato dalle regole correnti; recuperabile da Git |
| `docs/ROADMAP_V1_1.md` | `HISTORY` | roadmap 1.1 completata |
| `docs/RUNBOOKS.md` | `KEEP` | ingresso canonico breve per setup, sviluppo, test, operazioni e release |
| `docs/SETUP_AND_TEST.md` | `KEEP` | runbook setup e test corrente |
| `docs/TEST_READINESS_20260704.md` | `HISTORY` | snapshot di readiness datato |
| `docs/TEST_REPORT_20260704.md` | `HISTORY` | rapporto test datato |
| `docs/VIRGILIO_V112_INTEGRATION_ROADMAP.md` | `HISTORY` | roadmap di integrazione completata |
| `docs/VIRGILIO_V112_OPEN_QUESTIONS.md` | `HISTORY` | decisioni aperte storiche della roadmap completata |
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
| `local_connector/README.md` | `HISTORY` | assorbito in `docs/RUNBOOKS.md` da `CONS-D03` |
| `local_connector/tests/README.md` | `KEEP` | guida distinta alla suite locale |
