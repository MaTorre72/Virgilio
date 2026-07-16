# Next Codex Tasks

- Task corrente: `GATE U-H2 - Collaudo umano del percorso verticale`, stato
  `WAITING_HUMAN_REVIEW`.
- Prerequisiti soddisfatti: `GUI-U-E2-T01` - `GUI-U-E2-T07 = DONE`; le quattro
  anomalie del collaudo precedente hanno test specifici verdi.
- Azione necessaria unica: ripetere lo scenario della scheda gate e registrare
  un esito umano esplicito `PASS` oppure `FAIL` con l'area da correggere.
- Vincolo architetturale: `gui`/`gui_*` sono un'implementazione legacy
  abbandonata; `Caronte Manutenzione` resta target con una nuova presentazione
  `maintenance_gui` separata e consumer dei servizi condivisi.
- Nessun task E3 e` avviabile prima del nuovo `PASS` umano esplicito.

Dettagli, dipendenze ed evidenze: `docs/GUI_U_BACKLOG.md`.
