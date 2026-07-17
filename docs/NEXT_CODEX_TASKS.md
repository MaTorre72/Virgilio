# Next Codex Tasks

- Task corrente: `GUI-U-E3-T11 - Avvio automatico della distribuzione installata`.
- Stato: `BLOCKED`; la dipendenza `GUI-U-E3-T10 = DONE` e` soddisfatta, ma il
  build gate non produce l'eseguibile aggiornato: Tcl/Tk non si inizializza in
  tutte le toolchain locali gia` predisposte.
- Risultato: Caronte installato puo` avviarsi all'accesso a Windows senza
  dipendere dal repository o da componenti di sviluppo.
- Azione unica necessaria: ripristinare una toolchain Python Windows completa
  con Tcl/Tk funzionante per la build, quindi rieseguire T11 dall'inizio.
- Successivo: `GATE U-H3 - Collaudo utente finale`.
- `GATE U-H3` resta `WAITING_FOR_PREVIOUS_TASKS` fino alla chiusura di T11.
- Prima del nuovo collaudo: registrare il client OAuth Desktop centrale e
  fornirlo all'input protetto della build; nessun utente configurera` progetti.

Dettagli, criteri ed evidenze: `docs/GUI_U_BACKLOG.md`.
