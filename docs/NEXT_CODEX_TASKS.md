# Next Codex Tasks

- Iniziativa: `GUI-U = RECOVERY_BLOCKED`.
- Fase: `GUI-U-R - Recupero prodotto e collaudo osservabile`.
- Task completati: `GUI-U-R01 - Identita certa della build e dell'installer`; `GUI-U-R02-T01 - Percorso dimostrativo isolato`.
- Task corrente: `GUI-U-R02-T02 - Schermate del primo avvio osservabili` (`BLOCKED`).
- Blocco: il runtime di test non inizializza Tcl/Tk (`init.tcl` assente) e la
  venv di build non avvia Python (`Accesso negato`), quindi non sono ottenibili
  screenshot e prove a 960x640/100%/125%.
- Azione unica: ripristinare un runtime Python Windows eseguibile con Tcl/Tk
  completo; poi rieseguire `GUI-U-R02-T02` dall'inizio.
- Successivo: nessuno finche` `GUI-U-R02-T02` non e` `DONE`.
- Esito terminale obbligatorio R02-T03: `WAITING_HUMAN_REVIEW`; Codex non puo
  dichiarare il `PASS`. Solo dopo l'approvazione umana e` avviabile R03.

Dettagli, criteri ed evidenze: `docs/GUI_U_BACKLOG.md` e
`docs/GUI_U_HUMAN_ACCEPTANCE.md`.
