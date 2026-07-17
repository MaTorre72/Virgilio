# Next Codex Tasks

- Task corrente: `GUI-U-E3-T06 - Installer Windows`, stato `BLOCKED`.
- Dipendenza soddisfatta: `GUI-U-E3-T05 = DONE`.
- Risultato richiesto: rendere Caronte installabile e disinstallabile su Windows,
  mantenendo separati i dati utente dai file del programma.
- Vincolo architetturale: l'installer consuma la build one-folder gia` verificata;
  pubblicazione, firma commerciale e aggiornamento automatico restano fuori task.
- Blocco: la toolchain portabile non inizializza Tcl/Tk; la distribuzione Python
  completa richiede un'esecuzione elevata esplicitamente autorizzata dopo errore
  Windows Installer `2503`.
- Unica azione necessaria: autorizzare esplicitamente l'installazione elevata
  della toolchain completa nella cartella di build ignorata, poi rieseguire
  `GUI-U-E3-T06`.
- `GATE U-H3` resta non avviabile.

Dettagli, dipendenze ed evidenze: `docs/GUI_U_BACKLOG.md`.
