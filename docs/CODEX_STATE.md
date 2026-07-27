# Codex State

- Branch attesa: `codex/v1.1-development`.
- Modalita`: run autonoma ogni 30 minuti, seriale, un task e massimo un commit per run.
- Iniziativa: `GUI-U-R05 - Chiusura strutturale del percorso operativo` (`WAITING_HUMAN_REVIEW`).
- Task corrente: `GUI-U-R05-T09` `DONE`, correttivo coordinato nato dal
  FAIL reale del collaudo del 2026-07-27: retry Limbo, ripresa waiting,
  completion periodico, Registro operativo deduplicato e UIDVALIDITY di sessione.
  Prove: core `49 passed`, pipeline/polling `118 passed`, suite e smoke `593 passed`.
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
- Sequenza automatica residua: nessuna. Reset TEST e nuovo collaudo restano
  azioni separate da autorizzare; deployment Apps Script `40` resta invariato e
  la RC locale installata e` `0.11.0-1f0e6e8`.
- Pubblicazione Apps Script autorizzata e completata il 2026-07-27: push dei
  14 file canonici e deployment web esistente aggiornato alla versione `40`,
  senza cambiare URL. Il tab Registro e` canonico `bucoliche`; il reset usa il
  fallback canonico `Virgilio_Inbox` se la proprieta` legacy e` assente.
- RC desktop installata dal commit `1f0e6e8`: installer
  `CaronteSetup-0.11.0-1f0e6e8.exe`, Build ID
  `a0bb673d-6d1d-417f-9d26-cb8d5de71600`, SHA-256
  `5A2405EC861F2CE3654C0CF01D32857FEB496A8218042FC715CE6832C515E5D2`;
  build e smoke installer `PASS`, payload installato verificato e dati preservati.
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
