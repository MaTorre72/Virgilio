# Codex State

- Branch attesa: `codex/v1.1-development`.
- Modalita`: run autonoma ogni 30 minuti, seriale, un task e massimo un commit per run.
- Iniziativa: `GUI-U-R05 - Chiusura strutturale del percorso operativo` (`WAITING_HUMAN_REVIEW`).
- Task corrente: `GUI-U-R05-T08` correttivo coordinato `DONE` e distribuito;
  resta soltanto il collaudo finale umano.
- `GUI-U-R05-T01` e` `DONE`: un duplicato viene riusato solo con file e SHA-256 validi;
  file assenti o corrotti sono riacquisiti dal processor esistente; gli errori storage sono
  persistiti, visibili e bloccano handoff/completion. Prove: mirati `79 passed`, smoke `558 passed`.
- `GUI-U-R05-T02` e` `DONE`: pipeline e reset condividono il lock interprocesso; il runner
  posseduto viene fermato, il backup e` verificato prima delle modifiche, configurazione e
  credenziali restano, DB/quarantena sono ricreati e il ciclo fake successivo riacquisisce/copia.
  Prove: mirati `75 passed`, smoke `563 passed`.
- `GUI-U-R05-T03` e` `DONE`: una sola operazione coordinata espone l'anteprima esatta,
  prepara backup locali/Registro/Limbo, rifiuta asset non TEST o ID duplicati, riprende per
  `reset_id` senza duplicazioni e verifica i quattro stati vuoti con schema preservato. Il
  Limbo canonico e` piatto: i nomi includono gia` alias e attachment ID; il reset ricorsivo
  salva e rimuove eventuali sottocartelle pregresse. Regressione: mirati `71 passed`, smoke
  `577 passed`.
- Principio vincolante: CLI, servizi applicativi e GAS precedenti restano canonici e vanno riusati;
  non si ricostruiscono downloader, storage, verify, intake, Registro, backup o reset gia` esistenti.
- `GUI-U-R05-T04` e` `DONE`: audit a transizioni, export idempotente e percorso integrato
  email -> Limbo -> Da archiviare -> Registro sono verificati; prove `45 passed`, smoke `572 passed`.
- `GUI-U-R05-T07` e` `DONE`: la nuova strategia `move_to_done_label` aggiunge
  `traghettate` e rimuove la sola etichetta di ingresso tramite estensione Gmail,
  senza `DELETE`, `MOVE` o `EXPUNGE`; la copia-only precedente resta disponibile.
  Prove: mirati `73 passed`, smoke `581 passed`.
- `GUI-U-R05-T08` e` `DONE`: la pipeline conclude la mail solo quando ogni
  `Virgilio_Inbox` correlato e` `archiviato`; COPY/STORE e` seguito dalla verifica
  read-only delle due etichette; il reset preserva e verifica `Clienti_Siti`, `Team`
  e `TipiPratica`, ripristinabili solo da backup esplicito senza sovrascritture.
  Prove finali dopo l'allineamento live: mirati reset `13 passed`, regressione e
  smoke `589 passed`.
- Sequenza automatica residua: nessuna.
- Pubblicazione Apps Script autorizzata e completata il 2026-07-27: push dei
  14 file canonici e deployment web esistente aggiornato alla versione `40`,
  senza cambiare URL. Il tab Registro e` canonico `bucoliche`; il reset usa il
  fallback canonico `Virgilio_Inbox` se la proprieta` legacy e` assente.
- RC desktop installata dal commit `60cc6ff`: installer
  `CaronteSetup-0.11.0-60cc6ff.exe`, Build ID
  `b93b7fa7-60ca-462f-9ae7-1e7dc7cae0f6`, SHA-256
  `9EBDBB53A0378F8D6C0AD209A2E4BA8D0564F948AA87B4C90B87C8E86E92E685`;
  build e smoke installer `PASS`.
- Topologia TEST riallineata senza nuovi asset: GAS e Local connector usano lo
  stesso Registro umano append-only `bucoliche` con le stesse 17 colonne;
  stato e conflitti tecnici restano locali e non producono tab cloud paralleli.
  `Virgilio_Inbox` resta la sola coda operativa.
  `Staging_Local_Test` e le relative proprieta` non fanno piu` parte della topologia live.
- RC installata e `VIRGILIO_TOKEN` salvato nel deposito protetto locale su conferma
  umana del 2026-07-26.
- Anagrafiche ripristinate il 2026-07-27 dalla fonte storica verificata: 4 righe
  `Clienti_Siti`, 4 righe `Team`, 13 righe `TipiPratica`, confronto esatto riuscito.
- Reset TEST reale `reset-r05-20260727-t08-final` completato: backup locale,
  backup Registro e backup Limbo verificati; `bucoliche`, `Virgilio_Inbox` e
  Limbo sono vuoti, mentre le tre anagrafiche sono rimaste invariate. Configurazione,
  credenziali e machine ID locali preservati. Trigger TEST fermo.
- Gate residuo: solo collaudo finale umano. Codex non puo` approvarlo.
- `gui`/`gui_*` sono `ABANDONED_LEGACY`; target ammessi: `user_app` e `maintenance_gui`.
- Le RC precedenti non sono valide per il collaudo finale; le evidenze storiche restano in
  `docs/GUI_U_BACKLOG.md`.
- Contesto normale per una run: `AGENTS.md`, questo file e `docs/NEXT_CODEX_TASKS.md`.
