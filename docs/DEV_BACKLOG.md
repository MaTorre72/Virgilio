# Backlog di sviluppo

Stati: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`. Ordine operativo: priorità, poi ordine di tabella.

## Milestone 1 — Stabilizzazione pilota locale

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P0 | Refresh `Bucoliche_Stato` derivato dagli eventi | `bucoliche.py`, CLI, test | fake Sheet; idempotenza; Eventi immutato | Medio |
| DONE | P0 | `pilot-run-safe`: sequenza completa controllata | pipeline, CLI | dry-run senza effetti; stop su gate | Alto |
| DONE | P1 | Report pilota finale leggibile | pipeline, reports | fixture; JSON sicuro e sintesi umana | Basso |
| DONE | P1 | Idempotenza end-to-end | SQLite, Bucoliche, test | doppio run senza duplicati | Alto |
| DONE | P1 | Eliminare `example.invalid` da dati operativi | manifest/state | fixture realistica; nessun placeholder esportato | Medio |
| DONE | P1 | Gestire `attachment_id=None` | state/export | legacy fixture; skip `legacy_incomplete` | Medio |
| DONE | P1 | Verificare secondo export già esportato | Bucoliche test | zero append al retry | Medio |

## Milestone 2 — Usabilità minima

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P1 | Comando unico `virgilio pilot` | CLI | help, dry-run, exit code | Medio |
| DONE | P1 | Output umano oltre JSON | CLI/report | snapshot essenziale | Basso |
| TODO | P1 | Configurazione guidata | config/CLI | nessun segreto; config valida | Medio |
| TODO | P1 | Diagnostica errori comuni | doctor | fixture errori noti | Basso |
| TODO | P2 | README “10 comandi essenziali” | README | comandi verificati | Basso |

## Milestone 3 — Multi-postazione

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P1 | Simulare due `machine_id` | test/audit | fixture isolate | Medio |
| TODO | P1 | Merge eventi da due export | Bucoliche | ordine deterministico | Alto |
| TODO | P1 | Stato consolidato cross-machine | Bucoliche_Stato | una riga/fingerprint | Alto |
| TODO | P1 | Conflitti cross-machine | conflict detector | collisioni rilevate | Alto |
| TODO | P2 | Policy manuale risoluzione conflitti | docs/state | nessuna risoluzione automatica | Medio |

## Milestone 4 — Parsing allegati

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P2 | Confronto Docling/Unstructured su fixture | spike isolato | report qualità; nessuna produzione | Medio |
| TODO | P2 | Estrazione testo e tabelle senza AI | parser | fixture PDF/DOCX/XLSX | Alto |
| TODO | P2 | Manifest arricchito | manifest | schema retrocompatibile | Medio |

## Milestone 5 — Classificazione assistita

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P3 | Gateway LiteLLM | adapter futuro | mock provider; budget | Alto |
| TODO | P3 | Proposta classificazione | classifier futuro | nessuna azione automatica | Alto |
| TODO | P3 | Human review | workflow futuro | conferma obbligatoria | Alto |
| TODO | P3 | Feedback loop | audit futuro | correzioni tracciate | Alto |

## Registro avanzamento

- 2026-06-29 - Report pipeline arricchito con `human_summary` leggibile e sicura; test report verdi.
- 2026-06-29 - `pilot-run-safe` aggiunto come wrapper dry-run con stop su gate; test CLI/sequenza verdi.
- 2026-06-29 - `Bucoliche_Stato` rigenerato dagli eventi durante export; test fake/idempotenza verdi.
- 2026-06-30 - Doppio run end-to-end reso idempotente: export Bucoliche ignora eventi senza fingerprint e la completion registra eventi per allegato solo al primo completamento utile.
- 2026-06-30 - Manifest e SQLite usano l'email operativa risolta da `username_env` quando disponibile, evitando l'export di `example.invalid` dai config placeholder.
- 2026-06-30 - Export centrale e Bucoliche ora saltano i record legacy con `attachment_id=None` rilevati come `legacy_incomplete`, senza toccare gli eventi sintetici validi.
- 2026-06-30 - Aggiunto test di regressione sul secondo export Bucoliche già marcato `exported`: nessun nuovo append su `Bucoliche_Eventi`, `Bucoliche_Stato` continua a rigenerarsi.
- 2026-06-30 - Aggiunto il comando unico `virgilio pilot`: wrapper dry-run con preview integrato, exit code coerente ed entrypoint console dedicato.
- 2026-06-30 - `run-local-pipeline`, `pilot-preview`, `pilot-run-safe` e `virgilio pilot` supportano `--human` per uno snapshot leggibile, mantenendo il JSON come output predefinito per script e automazioni.
