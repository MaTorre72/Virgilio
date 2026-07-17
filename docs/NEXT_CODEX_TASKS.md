# Next Codex Tasks

- Task corrente: `GUI-U-E3-T09 - Accesso alle caselle Google`.
- Stato: `BLOCKED`; nessun codice puo` essere avviato prima della decisione sul
  percorso di accesso Google.
- Risultato: l'accesso Gmail/Workspace deve essere guidato e comprensibile dalla
  GUI utente senza richiedere configurazioni tecniche implicite.
- Dipendenze soddisfatte: `GUI-U-E3-T07 = DONE`, `GUI-U-E3-T08 = DONE`;
  `GATE U-H3 = FAIL` umano.
- Successivi: `GUI-U-E3-T10 - Registro e collegamento Google comprensibili`,
  poi `GUI-U-E3-T11 - Avvio automatico della distribuzione installata`.
- `GATE U-H3` resta `WAITING_FOR_PREVIOUS_TASKS` fino alla chiusura di T09-T11.
- Azione necessaria unica: scegliere OAuth come unico percorso oppure OAuth
  predefinito con password per app come fallback amministrato.

Dettagli, criteri ed evidenze: `docs/GUI_U_BACKLOG.md`.
