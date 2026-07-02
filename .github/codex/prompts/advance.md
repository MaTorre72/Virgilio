Leggi `AGENTS.md`, `docs/DEV_BACKLOG.md`, `docs/DEFINITION_OF_DONE.md` e `docs/AUTONOMOUS_DEVELOPMENT.md`.
Verifica branch `codex/v1.1-development` e working tree. Se il gate fallisce, fermati senza modifiche.

Questo prompt e` per il run orario di "Virgilio sviluppo autonomo": esegui un solo task per run e non
avviare un secondo task se il precedente non e` chiuso.

Se in `docs/DEV_BACKLOG.md` esiste il Task 0.0, esegui prima quello e non passare ai task v1.1.3 finche`
la separazione tra sorgente Apps Script e snapshot `clasp` non e` completata e verificata.

Altrimenti scegli il primo task P0/P1 `TODO` non bloccato, coerente con l`ordine operativo e con le
dipendenze gia` soddisfatte. Implementa la minima modifica sicura.

Se tocchi codice, esegui test mirati e smoke. Se tocchi solo documentazione, verifica i file aggiornati.
Aggiorna backlog e documentazione minima, crea un commit atomico e lascia il working tree pulito.

Non usare mail, Google o credenziali reali.
Non riscrivere il form, non sostituire Apps Script con Python, non introdurre AI/RAG/Docling/LiteLLM,
database remoti, server web o nuove GUI.

Se non ci sono task eleggibili o il backlog della milestone e` chiuso, limita l`output a una nota concisa
e non avviare nuovi lavori.
Se incontri credenziali, dipendenze esterne o limiti di accesso, registra il blocco in modo conciso e fermati.
