# Next Codex Tasks

Stato operativo corrente: backlog v1.1.3 attivo; chiuso `V113-E6-T02 - Creare comandi e verifiche semplici`, prossima run da `V113-E6-T03 - Distinguere test e produzione`.

## V113-E4-T01 - Adapter Local connector verso Da archiviare
- Stato: DONE nel workspace; `build_da_archiviare_intake_payload()` definisce il contratto metadata-only senza test_mode.
- Obiettivo: portare il local connector nel flusso unico senza inviare byte, base64 o path locali ad Apps Script.
- Input: quarantena, scan, manifest, metadata locali e file clean gia pronti per il Limbo.
- Output: file clean nel Limbo, record `Da archiviare`, evento Registro, idempotenza su secondo run.
- File probabili: `local_connector/`, `docs/ARCHITETTURA_UNIFICATA.md`, `docs/DEV_BACKLOG.md`.
- Criteri di accettazione: il secondo run non duplica, il payload resta metadata-only, non vengono inviati byte, base64 o path locali ad Apps Script, il perimetro local connector resta preservato, i test locali pertinenti restano verdi.
- Cosa non fare: non introdurre nuovi ingressi, non introdurre nuove GUI, non introdurre server o database remoti, non usare servizi reali, non modificare Apps Script salvo necessita esplicita del task.
- Conseguenza: la prossima run puo` partire da `V113-E5-T03 - Aggiornare stato e notifica dopo archiviazione`.

## V113-E5-T02 - Collegare submit al record inbox corretto
- Stato: DONE nel workspace; submit legato al record corretto e idempotente.
- Obiettivo: mantenere stabile la correlazione del submit con il `Virgilio_Inbox` giusto.
- Input: form attuale, `inbox_id` e record inbox.
- Output: submit idempotente sul record corretto senza creare un nuovo inbox.
- File probabili: Apps Script webapp e logica submit.
- Criteri di accettazione: correlazione stabile e idempotente.
- Cosa non fare: non usare il submit per aprire un inbox nuovo.

## V113-E5-T03 - Aggiornare stato e notifica dopo archiviazione
- Stato: DONE nel workspace; `doPost` ora propaga lo stato finale `archiviato`, la notifica dedicata riporta il finale e la schermata di successo mostra l'esito inbox.
- Obiettivo: rendere leggibile l'esito finale dopo l'archiviazione.
- Input: submit completato, record inbox e notifiche finali.
- Output: stato e notifica coerenti dopo l'archiviazione.
- File probabili: Apps Script, docs.
- Criteri di accettazione: esito finale leggibile e tracciato.
- Cosa non fare: non cambiare la UX in modo invasivo.
- Conseguenza: la prossima run puo` partire da `V113-E6-T02 - Creare comandi e verifiche semplici`.

## V113-E6-T01 - Documentare i due profili operativi
- Stato: DONE nel workspace; i due profili sono distinti in README, architettura e workflow clasp.
- Obiettivo: distinguere profilo Google-only e Local connector.
- Input: README, docs e verifiche di setup.
- Output: documentazione chiara sui due profili e sui controlli necessari.
- File probabili: `README.md`, `docs/ARCHITETTURA_UNIFICATA.md`, `docs/CLASP_WORKFLOW.md`.
- Criteri di accettazione: un operatore capisce subito il profilo attivo.
- Cosa non fare: non esporre fingerprint, manifest o SQLite nella UX normale.

## V113-E6-T02 - Creare comandi e verifiche semplici
- Stato: DONE nel workspace; comandi essenziali e verifiche minime allineati.
- Obiettivo: rendere lineari i comandi e i controlli minimi per il profilo attivo.
- Input: README, `docs/CLASP_WORKFLOW.md`.
- Output: comandi brevi e verifiche chiare per setup e controllo.
- File probabili: `README.md`, `docs/CLASP_WORKFLOW.md`.
- Criteri di accettazione: chi avvia Virgilio capisce subito cosa eseguire.
- Cosa non fare: non introdurre nuovi tool o flussi inutili.
