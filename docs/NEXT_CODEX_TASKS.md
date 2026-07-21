# Next Codex Tasks

- Iniziativa: `GUI-U = RECOVERY_IN_PROGRESS`.
- Fase: `GUI-U-R - Recupero prodotto e collaudo osservabile`.
- Task completati: `GUI-U-R01 - Identita certa della build e dell'installer`; `GUI-U-R02-T01 - Percorso dimostrativo isolato`; `GUI-U-R02-T02 - Schermate del primo avvio osservabili`.
- Task corrente: `GUI-U-R02-T03 - Home dimostrativa ed evidenze installate` (`TODO`).
- Dipendenza: `GUI-U-R02-T02 = DONE`.
- Blocco: nessuno. Il runtime locale inizializza Tcl/Tk `8.6.15` e la prova reale di resize R02-T02 e` verde.
- Successivo: completare `GUI-U-R02-T03`; il suo esito terminale e` `WAITING_HUMAN_REVIEW`.
- Esito terminale obbligatorio R02-T03: `WAITING_HUMAN_REVIEW`; Codex non puo
  dichiarare il `PASS`. Solo dopo l'approvazione umana e` avviabile R03.

Dettagli, criteri ed evidenze: `docs/GUI_U_BACKLOG.md` e
`docs/GUI_U_HUMAN_ACCEPTANCE.md`.
