# Next Codex Tasks

- Task corrente: `GUI-U-E2-T07 - Correzioni dal collaudo verticale`, stato `TODO`.
- Risultato richiesto: stato `Casella attiva` coerente, conclusione esplicita
  del wizard verso la Home, configurazione riapribile dalla Home e controlli
  finestra chiaramente disponibili.
- Dipendenza soddisfatta: `GUI-U-E2-T06 = DONE`; `GATE U-H2` ha ricevuto esito
  umano `FAIL` il 2026-07-16 e attende la correzione prima del nuovo collaudo.
- Vincolo architetturale: `gui`/`gui_*` sono un'implementazione legacy
  abbandonata; `Caronte Manutenzione` resta target con una nuova presentazione
  `maintenance_gui` separata e consumer dei servizi condivisi.
- Dopo `GUI-U-E2-T07`: ripetere `GATE U-H2`; nessun task E3 e` avviabile prima
  del nuovo `PASS` umano esplicito.

Dettagli, dipendenze ed evidenze: `docs/GUI_U_BACKLOG.md`.
