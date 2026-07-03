# Next Codex Tasks

Ordine operativo per il prossimo sviluppo autonomo.

## V113-00-T01 - Separazione sorgente/snapshot Apps Script

- Stato: DONE nel workspace; sorgente canonica in `apps_script/src` e snapshot `clasp` in `apps_script/clasp`.
- Conseguenza: la prossima run puo partire dai task v1.1.3 senza riaprire questo punto.

## V113-E0-T01 - Mappa funzioni divergenti Google-only/local connector

- Stato: DONE nel workspace; mappa minima delle funzioni da preservare in `docs/ARCHITETTURA_UNIFICATA.md`.
- Conseguenza: la prossima run puo` partire da `V113-E0-T02`.

## V113-E0-T02 - Mappa lessico legacy -> lessico ufficiale

- Obiettivo: tradurre i termini tecnici storici nel lessico utente ufficiale.
- Input: documenti esistenti, README, backlog, note operative.
- Output: tabella di equivalenza legacy/ufficiale.
- File probabili: `docs/ARCHITETTURA_UNIFICATA.md`, `docs/DEV_BACKLOG.md`, `AGENTS.md`.
- Accettazione: `staging`, `Bucoliche_*`, `Virgilio_Inbox` e termini correlati sono spiegati in modo coerente.
- Cosa non fare: non cambiare i nomi tecnici nel codice se crea rischio.

## V113-E1-T01 - Definisci schema Registro unico

- Stato: DONE nel workspace; schema minimo del Registro definito in `docs/ARCHITETTURA_UNIFICATA.md`.
- Conseguenza: la prossima run puo partire da `V113-E2-T01`.

## V113-E2-T01 - Definisci schema Da archiviare

- Obiettivo: formalizzare la coda operativa `Virgilio_Inbox` come `Da archiviare`.
- Input: flusso form, record inbox, casi legacy.
- Output: schema minimo, campi obbligatori e stati.
- File probabili: `docs/ARCHITETTURA_UNIFICATA.md`, `docs/DEV_BACKLOG.md`.
- Accettazione: una sola riga operativa per documento, con idempotenza.
- Cosa non fare: non trattare la coda come archivio storico.

## V113-E3-T01 - Adapter Google-only verso Da archiviare

- Obiettivo: far entrare `GmailApp` nel flusso unico verso `Da archiviare`.
- Input: Google Apps Script attuale e schema inbox.
- Output: riga inbox e evento Registro dopo il salvataggio nel Limbo.
- File probabili: Apps Script del progetto reale, `docs/CLASP_WORKFLOW.md`.
- Accettazione: il percorso Google-only crea record operativi senza archiviazione automatica.
- Cosa non fare: non usare Bucoliche come coda utente.

## V113-E4-T01 - Adapter Local connector verso Da archiviare

- Obiettivo: portare il local connector nel flusso unico senza inviare path locali ad Apps Script.
- Input: quarantena, scan, manifest e metadata locali.
- Output: file clean nel Limbo, riga inbox e evento Registro.
- File probabili: `local_connector/`, `docs/ARCHITETTURA_UNIFICATA.md`.
- Accettazione: secondo run non duplica e il payload resta metadata-only.
- Cosa non fare: non mandare byte, base64 o path locali ad Apps Script.

## V113-E5-T01 - Form unico con `inbox_id`

- Obiettivo: mantenere un solo form che funzioni sia manualmente sia da `Da archiviare`.
- Input: form attuale e record inbox.
- Output: form con apertura manuale legacy e contesto documento via `inbox_id`.
- File probabili: Apps Script webapp, HTML del form, `docs/CLASP_WORKFLOW.md`.
- Accettazione: il form apre la pratica in entrambi i casi e aggiorna il record corretto.
- Cosa non fare: non riscrivere la UX in modo invasivo.

## V113-E6-T01 - UX/configurazione profili

- Obiettivo: distinguere bene profilo Google-only e profilo Local connector.
- Input: README, docs, comandi di setup e verifica.
- Output: documentazione e comandi semplici per capire quale profilo si sta usando.
- File probabili: `README.md`, `docs/ARCHITETTURA_UNIFICATA.md`, `docs/CLASP_WORKFLOW.md`.
- Accettazione: un operatore capisce subito il profilo attivo e i controlli necessari.
- Cosa non fare: non esporre fingerprint, manifest o SQLite nella UX normale.
