# Next Codex Tasks

Stato operativo corrente: backlog v1.1.3 attivo; chiuso `V113-E4-T03 - Creare record Da archiviare dal local connector`, prossima run da `V113-E4-T04 - Scrivere evento Registro dal percorso locale`.

## V113-E4-T01 - Adapter Local connector verso Da archiviare
- Stato: DONE nel workspace; `build_da_archiviare_intake_payload()` definisce il contratto metadata-only senza test_mode.
- Obiettivo: portare il local connector nel flusso unico senza inviare byte, base64 o path locali ad Apps Script.
- Input: quarantena, scan, manifest, metadata locali e file clean gia pronti per il Limbo.
- Output: file clean nel Limbo, record `Da archiviare`, evento Registro, idempotenza su secondo run.
- File probabili: `local_connector/`, `docs/ARCHITETTURA_UNIFICATA.md`, `docs/DEV_BACKLOG.md`.
- Criteri di accettazione: il secondo run non duplica, il payload resta metadata-only, non vengono inviati byte, base64 o path locali ad Apps Script, il perimetro local connector resta preservato, i test locali pertinenti restano verdi.
- Cosa non fare: non introdurre nuovi ingressi, non introdurre nuove GUI, non introdurre server o database remoti, non usare servizi reali, non modificare Apps Script salvo necessita esplicita del task.
- Conseguenza: la prossima run puo` partire da `V113-E4-T04 - Scrivere evento Registro dal percorso locale`.

## V113-E5-T01 - Form unico con inbox_id
- Obiettivo: mantenere un solo form che funzioni sia manualmente sia da `Da archiviare`.
- Input: form attuale, record inbox e note operative.
- Output: apertura manuale e via `inbox_id` senza riscrittura invasiva.
- File probabili: Apps Script webapp, HTML del form, `docs/CLASP_WORKFLOW.md`.
- Criteri di accettazione: il form apre la pratica in entrambi i casi e aggiorna il record corretto.
- Cosa non fare: non cambiare la UX in modo invasivo.

## V113-E6-T01 - Documentare i due profili operativi
- Obiettivo: distinguere profilo Google-only e profilo Local connector.
- Input: README, docs e verifiche di setup.
- Output: documentazione chiara sui due profili e sui controlli necessari.
- File probabili: `README.md`, `docs/ARCHITETTURA_UNIFICATA.md`, `docs/CLASP_WORKFLOW.md`.
- Criteri di accettazione: un operatore capisce subito il profilo attivo.
- Cosa non fare: non esporre fingerprint, manifest o SQLite nella UX normale.
