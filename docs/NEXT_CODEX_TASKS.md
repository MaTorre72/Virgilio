# Next Codex Tasks

- Task corrente: `GATE U-H2 - Collaudo umano del percorso verticale`, stato `WAITING_HUMAN_REVIEW`.
- Prerequisiti soddisfatti: `GUI-U-E2-T01` - `GUI-U-E2-T06 = DONE`.
- Vincolo architetturale: `gui`/`gui_*` sono un'implementazione legacy
  abbandonata; `Caronte Manutenzione` resta target con una nuova presentazione
  `maintenance_gui` separata e consumer dei servizi condivisi.
- Nessun task successivo e` avviabile prima del `PASS` umano esplicito.

Dettagli, dipendenze ed evidenze: `docs/GUI_U_BACKLOG.md`.
