# Next Codex Tasks

Stato operativo corrente: backlog v1.1.3 attivo e lettura minima per la prossima run.

## V113-E4-T01 - Preservare il perimetro local connector esistente
- Obiettivo: tenere intatto il perimetro local connector mentre si riallinea il flusso unico.
- Input: `local_connector/`, note architetturali e backlog attivo.
- Output: nessuna regressione locale mentre il resto del flusso si consolida.
- File probabili: `local_connector/`, `docs/ARCHITETTURA_UNIFICATA.md`, `docs/DEV_BACKLOG.md`.
- Criteri di accettazione: i test locali restano verdi e il perimetro non si allarga.
- Cosa non fare: non introdurre nuovi ingressi, nuove GUI o servizi remoti.

## V113-E5-T01 - Mantenere il form unico con fallback legacy
- Obiettivo: mantenere un solo form con apertura manuale e fallback legacy.
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
