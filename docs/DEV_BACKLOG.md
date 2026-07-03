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

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P0 | Preservare il perimetro local connector esistente | `local_connector/` | niente regressioni locali | Alto |
| TODO | P1 | Copiare solo file clean nel Limbo | `local_connector/` | niente byte o path locali verso Apps Script | Alto |
| TODO | P1 | Creare record `Da archiviare` dal local connector | `local_connector/`, Apps Script | idempotenza su secondo run | Alto |
| TODO | P1 | Scrivere evento Registro dal percorso locale | `local_connector/`, docs | audit unico e coerente | Alto |

### EPICA 5 - Form unico

Obiettivo: mantenere un solo form per apertura manuale e archiviazione da Limbo.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P0 | Mantenere il form unico con fallback legacy | Apps Script webapp, HTML | apertura manuale e via `inbox_id` | Alto |
| TODO | P1 | Collegare submit al record inbox corretto | Apps Script | correlazione stabile e idempotente | Alto |
| TODO | P1 | Aggiornare stato e notifica dopo archiviazione | Apps Script, docs | esito leggibile e tracciato | Medio |

### EPICA 6 - UX e configurazione

Obiettivo: rendere comprensibili i due profili operativi senza esporre dettagli tecnici inutili.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P1 | Documentare i due profili operativi | `README.md`, docs | chiarezza per utenti e tecnici | Medio |
| TODO | P1 | Creare comandi e verifiche semplici | `README.md`, `docs/CLASP_WORKFLOW.md` | setup e controllo lineari | Medio |
| TODO | P2 | Distinguere test e produzione | `README.md`, docs | nessuna ambiguita` operativa | Medio |
| TODO | P2 | Nascondere dettagli macchina nella UX normale | UI, docs | niente fingerprint, manifest o SQLite visibili | Medio |
