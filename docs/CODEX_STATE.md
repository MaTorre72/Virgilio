# Codex State

- Branch attesa: `codex/v1.1-development`.
- Modalita`: run autonoma ogni 30 minuti, seriale, un task e massimo un commit per run.
- Iniziativa: `GUI-U-R05 - Chiusura strutturale del percorso operativo` (`IN_PROGRESS`).
- Task corrente: `GUI-U-R05-T01 - Recupero artefatti locali e fallimento storage osservabile`.
- Diagnosi reale del 2026-07-26: 4 messaggi/5 allegati trovati; file di quarantena mancanti;
  `duplicate_seen` impedisce il nuovo download; storage restituisce `staging_failed` ma la pipeline
  termina senza errore; Limbo vuoto e nessun nuovo record `Da archiviare`.
- Principio vincolante: CLI, servizi applicativi e GAS precedenti restano canonici e vanno riusati;
  non si ricostruiscono downloader, storage, verify, intake, Registro, backup o reset gia` esistenti.
- Sequenza: `R05-T01` recupero e propagazione errore; `R05-T02` ripristino locale coordinato;
  `R05-T03` azzeramento coerente ambiente TEST; `R05-T04` audit non ripetitivo e RC finale.
- Gate umani futuri: autorizzazione `clasp push`/deploy, autorizzazione reset remoto reale e collaudo
  finale. Codex non puo` approvarli.
- `gui`/`gui_*` sono `ABANDONED_LEGACY`; target ammessi: `user_app` e `maintenance_gui`.
- Le RC precedenti non sono valide per il collaudo finale; le evidenze storiche restano in
  `docs/GUI_U_BACKLOG.md`.
- Contesto normale per una run: `AGENTS.md`, questo file e `docs/NEXT_CODEX_TASKS.md`.
