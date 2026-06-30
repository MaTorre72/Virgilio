# Backlog di sviluppo

Stati: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`. Ordine operativo: priorita, poi ordine di tabella.

## Milestone 1 - Stabilizzazione pilota locale

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P0 | Refresh `Bucoliche_Stato` derivato dagli eventi | `bucoliche.py`, CLI, test | fake Sheet; idempotenza; Eventi immutato | Medio |
| DONE | P0 | `pilot-run-safe`: sequenza completa controllata | pipeline, CLI | dry-run senza effetti; stop su gate | Alto |
| DONE | P1 | Report pilota finale leggibile | pipeline, reports | fixture; JSON sicuro e sintesi umana | Basso |
| DONE | P1 | Idempotenza end-to-end | SQLite, Bucoliche, test | doppio run senza duplicati | Alto |
| DONE | P1 | Eliminare `example.invalid` da dati operativi | manifest/state | fixture realistica; nessun placeholder esportato | Medio |
| DONE | P1 | Gestire `attachment_id=None` | state/export | legacy fixture; skip `legacy_incomplete` | Medio |
| DONE | P1 | Verificare secondo export gia esportato | Bucoliche test | zero append al retry | Medio |

## Milestone 2 - Usabilita minima

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P1 | Comando unico `virgilio pilot` | CLI | help, dry-run, exit code | Medio |
| DONE | P1 | Output umano oltre JSON | CLI/report | snapshot essenziale | Basso |
| DONE | P1 | Configurazione guidata | config/CLI | nessun segreto; config valida | Medio |
| DONE | P1 | Diagnostica errori comuni | doctor | fixture errori noti | Basso |
| DONE | P2 | README "10 comandi essenziali" | README | comandi verificati | Basso |

## Milestone 3 - Multi-postazione

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P1 | Simulare due `machine_id` | test/audit | fixture isolate | Medio |
| DONE | P1 | Merge eventi da due export | Bucoliche | ordine deterministico | Alto |
| DONE | P1 | Stato consolidato cross-machine | Bucoliche_Stato | una riga/fingerprint | Alto |
| DONE | P1 | Conflitti cross-machine | conflict detector | collisioni rilevate | Alto |
| DONE | P2 | Policy manuale risoluzione conflitti | docs/state | nessuna risoluzione automatica | Medio |

## Milestone 4 - Parsing allegati

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P2 | Confronto Docling/Unstructured su fixture | spike isolato | report qualita; nessuna produzione | Medio |
| DONE | P2 | Estrazione testo e tabelle senza AI | parser | fixture PDF/DOCX/XLSX | Alto |
| DONE | P2 | Manifest arricchito | manifest | schema retrocompatibile | Medio |

## Milestone 5 - Classificazione assistita

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P3 | Gateway LiteLLM | adapter futuro | mock provider; budget | Alto |
| DONE | P3 | Proposta classificazione | classifier futuro | nessuna azione automatica | Alto |
| DONE | P3 | Human review | workflow futuro | conferma obbligatoria | Alto |
| DONE | P3 | Feedback loop | audit futuro | correzioni tracciate | Alto |

## Registro avanzamento

- 2026-06-29 - Report pipeline arricchito con `human_summary` leggibile e sicura; test report verdi.
- 2026-06-29 - `pilot-run-safe` aggiunto come wrapper dry-run con stop su gate; test CLI/sequenza verdi.
- 2026-06-29 - `Bucoliche_Stato` rigenerato dagli eventi durante export; test fake/idempotenza verdi.
- 2026-06-30 - Doppio run end-to-end reso idempotente: export Bucoliche ignora eventi senza fingerprint e la completion registra eventi per allegato solo al primo completamento utile.
- 2026-06-30 - Manifest e SQLite usano l'email operativa risolta da `username_env` quando disponibile, evitando l'export di `example.invalid` dai config placeholder.
- 2026-06-30 - Export centrale e Bucoliche ora saltano i record legacy con `attachment_id=None` rilevati come `legacy_incomplete`, senza toccare gli eventi sintetici validi.
- 2026-06-30 - Aggiunto test di regressione sul secondo export Bucoliche gia marcato `exported`: nessun nuovo append su `Bucoliche_Eventi`, `Bucoliche_Stato` continua a rigenerarsi.
- 2026-06-30 - Aggiunto il comando unico `virgilio pilot`: wrapper dry-run con preview integrato, exit code coerente ed entrypoint console dedicato.
- 2026-06-30 - `run-local-pipeline`, `pilot-preview`, `pilot-run-safe` e `virgilio pilot` supportano `--human` per uno snapshot leggibile, mantenendo il JSON come output predefinito per script e automazioni.
- 2026-06-30 - Aggiunto `virgilio init-config`: genera uno scheletro `accounts.local.yaml` valido e senza segreti nel file, con sezioni account/storage/Bucoliche/rules e note sulle env locali.
- 2026-06-30 - `doctor` ora espone suggerimenti azionabili sugli errori ricorrenti e supporta `--human` per una diagnosi locale leggibile senza segreti.
- 2026-06-30 - Coperti nei test due `machine_id` isolati: `load_machine_id` resta stabile per root locale e l'export Bucoliche preview conserva due eventi distinti sullo stesso fingerprint.
- 2026-06-30 - L'export Bucoliche ora ordina gli eventi in modo deterministico per timestamp, fingerprint e macchina, cosi due export equivalenti da postazioni diverse producono lo stesso merge anche con `audit_events.id` invertiti.
- 2026-06-30 - `Bucoliche_Stato` ora consolida davvero il cross-machine: una sola riga per fingerprint, `machine_id` aggregati in modo deterministico e note marcate `cross_machine` quando lo stesso allegato arriva da piu postazioni.
- 2026-06-30 - `Bucoliche_Stato` segnala `conflict_cross_machine` quando lo stesso fingerprint arriva da piu macchine con esiti terminali incompatibili, includendo `machine_states` nelle note senza risoluzione automatica.
- 2026-06-30 - Aggiunto `litellm-gateway-dry-run`: adapter LiteLLM futuro mock-only con budget locale su token/costo, senza rete ne dipendenze LiteLLM, pronto per la futura classificazione assistita.
- 2026-06-30 - Documentata la policy manuale per `conflict_cross_machine`: triage su `state.db`, macchina autorevole unica, nessuna modifica manuale ai tab Bucoliche e nessuna risoluzione automatica.
- 2026-06-30 - `local_connector/README.md` ora include la sezione "10 comandi essenziali" con il flusso locale minimo v1.1 allineato alla CLI corrente.
- 2026-06-30 - Aggiunto `compare-parser-fixtures`, spike isolato che confronta snapshot Docling/Unstructured su fixture sintetiche e produce un report locale di qualita senza dipendenze o parsing reale.
- 2026-06-30 - Aggiunto `extract-local-fixtures`: parser locale `stdlib_local` che estrae testo e tabelle minime da fixture sintetiche `PDF/DOCX/XLSX` con sole librerie standard, fuori dalla pipeline produttiva.
- 2026-06-30 - Il manifest locale e staged ora include anche metadati retrocompatibili di provenienza e decisione (`source_sender`, `source_mailbox`, `source_message_date`, `source_thread_id`, `file_extension`, `policy_*`, `status_reason`) senza cambiare i consumer esistenti.
- 2026-06-30 - Aggiunto `classify-manifest-dry-run`: legge un manifest locale, propone una classificazione prudente con review obbligatoria e allega il responso mock LiteLLM senza reti o azioni automatiche.
- 2026-06-30 - Aggiunto `review-classification-dry-run`: accetta solo proposte locali `dry_run` con `review_required=true`, registra approvazione/rifiuto umano e mantiene il workflow futuro senza azioni automatiche.
- 2026-06-30 - Aggiunto `classification-feedback-dry-run`: accetta solo review locali `dry_run` completate, traccia la classificazione finale e distingue tra conferma e correzione manuale senza scrivere stato operativo.
