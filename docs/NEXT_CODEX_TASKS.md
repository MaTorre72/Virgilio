# Next Codex Tasks

- Task corrente: `GATE U-H3 - Collaudo umano di distribuzione`, stato
  `WAITING_HUMAN_REVIEW`.
- Prerequisiti: `GUI-U-E3-T01` - `GUI-U-E3-T06 = DONE`.
- Artefatto locale pronto:
  `local_connector\build-output\installer\dist\CaronteSetup.exe`.
- Scenario umano su PC o VM senza Python: installazione, primo avvio, due caselle,
  controllo, pausa, chiusura e riapertura, persistenza, avvio automatico e
  disinstallazione.
- Evidenze automatiche: test installer `9 passed`, suite e smoke locale
  `442 passed`, smoke installer isolato verde con dati sintetici preservati.
- Azione necessaria unica: comunicare esito umano esplicito `PASS`, oppure `FAIL`
  indicando l'area osservata; Codex non puo` approvare il gate.

Dettagli e istruzioni: `docs/GUI_U_BACKLOG.md`, sezione `GATE U-H3`.
