# Backlog di sviluppo

Nota: lo storico, i completamenti chiusi e le milestone finite sono stati spostati in
`docs/DEV_BACKLOG_ARCHIVE.md`; il registro datato e` in `docs/CHANGELOG_DEV.md`.
Le fonti operative leggere restano `docs/CODEX_STATE.md` e `docs/NEXT_CODEX_TASKS.md`.

Stati: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`. Qui restano solo task attivi o bloccati.

## Milestone v1.1.3 - Virgilio unificato

Obiettivo: consolidare Virgilio come un solo flusso operativo con due ingressi tecnici, lessico
comune e sviluppo Apps Script tramite `clasp`.

### EPICA 4 - Adapter Local connector

Obiettivo: portare `IMAP` locale nel flusso unico senza inviare dati locali ad Apps Script.

| ID | Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|---|
| V113-E4-T01 | DONE | P0 | Adapter Local connector verso Da archiviare | `local_connector/`, `docs/ARCHITETTURA_UNIFICATA.md`, `docs/DEV_BACKLOG.md` | secondo run non duplica, payload metadata-only, niente byte/base64/path locali verso Apps Script, test locali pertinenti verdi | Alto |
| V113-E4-T02 | DONE | P1 | Copiare solo file clean nel Limbo | `local_connector/` | stage_ready_files() copia solo file con `status='ready_for_caronte'`; test locali pertinenti verdi | Alto |
| V113-E4-T03 | DONE | P1 | Creare record `Da archiviare` dal local connector | `local_connector/`, Apps Script | `intake-da-archiviare` crea/aggiorna `Virgilio_Inbox` senza byte o path locali; retry identico idempotente | Alto |
| V113-E4-T04 | DONE | P1 | Scrivere evento Registro dal percorso locale | `local_connector/`, docs | audit unico e coerente | Alto |

### EPICA 5 - Form unico

Obiettivo: mantenere un solo form per apertura manuale e archiviazione da Limbo.

| ID | Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|---|
| V113-E5-T01 | DONE | P0 | Form unico con `inbox_id` | Apps Script webapp, HTML | apertura manuale e via `inbox_id` | Alto |
| V113-E5-T02 | DONE | P1 | Collegare submit al record inbox corretto | Apps Script | correlazione stabile e idempotente | Alto |
| V113-E5-T03 | DONE | P1 | Aggiornare stato e notifica dopo archiviazione | Apps Script, docs | esito leggibile e tracciato | Medio |

### EPICA 6 - UX e configurazione

Obiettivo: rendere comprensibili i due profili operativi senza esporre dettagli tecnici inutili.

| ID | Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|---|
| V113-E6-T01 | DONE nel workspace; README, architettura e workflow clasp allineati | P1 | Documentare i due profili operativi | `README.md`, docs | chiarezza per utenti e tecnici | Medio |
| V113-E6-T02 | DONE | P1 | Creare comandi e verifiche semplici | `README.md`, `docs/CLASP_WORKFLOW.md` | setup e controllo lineari | Medio |
| V113-E6-T03 | TODO | P2 | Distinguere test e produzione | `README.md`, docs | nessuna ambiguita` operativa | Medio |
| V113-E6-T04 | TODO | P2 | Nascondere dettagli macchina nella UX normale | UI, docs | niente fingerprint, manifest o SQLite visibili | Medio |
