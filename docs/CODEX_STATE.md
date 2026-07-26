# Codex State

- Branch attesa: `codex/v1.1-development`.
- Modalita`: run autonoma ogni 30 minuti, seriale, un task e massimo un commit per run.
- Iniziativa: `GUI-U-R05 - Chiusura strutturale del percorso operativo` (`WAITING_HUMAN_REVIEW`).
- Task corrente: `GUI-U-R05-T05` correttivo completato; reset TEST reale in attesa
  della sola chiave di collegamento nel deposito protetto locale.
- `GUI-U-R05-T01` e` `DONE`: un duplicato viene riusato solo con file e SHA-256 validi;
  file assenti o corrotti sono riacquisiti dal processor esistente; gli errori storage sono
  persistiti, visibili e bloccano handoff/completion. Prove: mirati `79 passed`, smoke `558 passed`.
- `GUI-U-R05-T02` e` `DONE`: pipeline e reset condividono il lock interprocesso; il runner
  posseduto viene fermato, il backup e` verificato prima delle modifiche, configurazione e
  credenziali restano, DB/quarantena sono ricreati e il ciclo fake successivo riacquisisce/copia.
  Prove: mirati `75 passed`, smoke `563 passed`.
- `GUI-U-R05-T03` e` `DONE`: una sola operazione coordinata espone l'anteprima esatta,
  prepara backup locali/Registro/Limbo, rifiuta asset non TEST o ID duplicati, riprende per
  `reset_id` senza duplicazioni e verifica i quattro stati vuoti con schema preservato.
  Prove: mirati `91 passed`, harness GAS puro `OK`, smoke `571 passed`.
- Principio vincolante: CLI, servizi applicativi e GAS precedenti restano canonici e vanno riusati;
  non si ricostruiscono downloader, storage, verify, intake, Registro, backup o reset gia` esistenti.
- `GUI-U-R05-T04` e` `DONE`: audit a transizioni, export idempotente e percorso integrato
  email -> Limbo -> Da archiviare -> Registro sono verificati; prove `45 passed`, smoke `572 passed`.
- Sequenza automatica residua: nessuna.
- Pubblicazione Apps Script autorizzata esplicitamente dall'utente e completata il 2026-07-26:
  push dei 14 file canonici e deployment web esistente aggiornato alla versione `33`,
  senza cambiare URL.
- Topologia TEST riallineata senza nuovi asset: il writer GAS storico usa `bucoliche`,
  la CLI usa esclusivamente `Bucoliche_Eventi`, `Bucoliche_Stato` e
  `Bucoliche_Conflitti`, mentre `Virgilio_Inbox` resta la sola coda operativa.
  `Staging_Local_Test` e le relative proprieta` non fanno piu` parte della topologia live.
- Il reset precedente non e` evidenza valida per la topologia corretta. L'unico trigger
  TEST e` stato fermato; il nuovo reset e` bloccato prima di backup/mutazioni perche`
  `Caronte/VIRGILIO_TOKEN` manca dal Credential Manager locale. Azione unica: reinserire
  la chiave nella schermata locale di collegamento, poi rieseguire il reset coordinato.
- Gate residui: ripetizione del reset TEST sulla topologia corretta e collaudo
  finale umano. Codex non puo` approvare il collaudo.
- `gui`/`gui_*` sono `ABANDONED_LEGACY`; target ammessi: `user_app` e `maintenance_gui`.
- Le RC precedenti non sono valide per il collaudo finale; le evidenze storiche restano in
  `docs/GUI_U_BACKLOG.md`.
- Contesto normale per una run: `AGENTS.md`, questo file e `docs/NEXT_CODEX_TASKS.md`.
