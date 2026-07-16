# Next Codex Tasks

- Task corrente: `GUI-U-E3-T05 - Build autonoma`, stato `TODO`.
- Dipendenza soddisfatta: `GUI-U-E3-T04 = DONE`.
- Risultato richiesto: produrre una build one-folder riproducibile che avvia
  `Caronte.exe` senza ambiente di sviluppo o repository.
- Vincolo architetturale: la build include `user_app` e i servizi condivisi ma
  esclude l'implementazione legacy `gui`/`gui_*`; installer e firma restano fuori task.
- Dopo `GUI-U-E3-T05`: `GUI-U-E3-T06 - Installer Windows`.

Dettagli, dipendenze ed evidenze: `docs/GUI_U_BACKLOG.md`.
