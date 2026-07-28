# Codex State

- Branch attesa: `codex/v1.1-development`.
- Modalita`: consolidamento autonomo ogni 60 minuti, seriale, un task e massimo
  un commit per run; Git usa solo fetch/pull fast-forward e push non forzato.
- Iniziativa corrente: `CONS - Pubblicazione, pulizia e consegna 1.1`, definita
  in `docs/CONSOLIDATION_PROGRAM.md`.
- Task corrente: `CONS-D01`, inventario documentale completo
  `KEEP/MERGE/HISTORY/REMOVE`.
- `CONS-R04` e` `DONE`: il tag annotato `v1.1.0` identifica il commit sorgente
  release `68f3b90`; annotazione, riferimento locale e riferimento remoto sono
  stati verificati e coincidono.
- `CONS-R03` e` `DONE`: dal commit pulito `68f3b90` sono stati prodotti
  `CaronteSetup-1.1.0-68f3b90.exe` e manifest; build e smoke installer `PASS`.
  Artefatto: 30.699.894 byte, SHA-256
  `8CD723E3DF14DFB30DE1E17D5BDDC29C81E3C87558DCBC85CA33828AE40DDE92`,
  Build ID `8268f442-8066-45c3-a9bc-0b32f6acdc76`; OAuth incluso.
- `CONS-R02` e` `DONE`: README e changelog presentano il percorso desktop 1.1
  collaudato, prerequisiti e limiti reali; `1.1.0` e` distinta dalle RC storiche
  `0.11.0-<commit>`. Prove: controlli documentali e smoke locale `600 passed`.
- `CONS-R01` e` `DONE`: `virgilio_connector._version.__version__` e` la sola
  fonte autorevole `1.1.0` letta da package metadata, runtime e build; `VERSION`
  e` il marcatore verificato. Prove: mirati `22 passed`, smoke `600 passed`.
- Iniziativa precedente: `GUI-U-R05 - Chiusura strutturale del percorso operativo` (`PASS`
  umano esplicito del 2026-07-28). `GUI-U` e `GATE U-H3` sono chiusi `PASS`.
- Ultimo task precedente: `GUI-U-R05-T11` `DONE`, correttivo nato dal caso reale
  del 2026-07-28: allegati annidati in `multipart/mixed` dentro
  `multipart/alternative`, identita` IMAP duplicate tra cicli e report senza
  avviso quando una mail rilevata produce zero allegati. Parser ricorsivo,
  identita` riusata e warning operativo sono coperti da mirati `132 passed`,
  suite e smoke `599 passed`. Nessun servizio reale e nessun byte della mail
  reale entrano nei test.
- `GUI-U-R05-T10` e` `DONE`, correttivo nato dal secondo FAIL reale
  del 2026-07-27: follow-up persistente di handoff/completion e rimozione Gmail
  eseguita dalla cartella destinazione tramite `X-GM-MSGID`. Nessuna nuova
  acquisizione nel follow-up e nessun `DELETE`, `MOVE` o `EXPUNGE`.
  Prove: mirati `146 passed`, suite e smoke `595 passed`; quattro mail reali
  completate, `da-traghettare` vuota e `traghettate` verificata.
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
- Sequenza automatica residua: nessuna. La RC contenente T11 e` installata;
  Apps Script `40` resta invariato e il collaudo umano finale e` `PASS`.
- Pubblicazione Apps Script autorizzata e completata il 2026-07-27: push dei
  14 file canonici e deployment web esistente aggiornato alla versione `40`,
  senza cambiare URL. Il tab Registro e` canonico `bucoliche`; il reset usa il
  fallback canonico `Virgilio_Inbox` se la proprieta` legacy e` assente.
- RC desktop installata dal commit `7e18277`: installer
  `CaronteSetup-0.11.0-7e18277.exe`, Build ID
  `04736b60-fca3-49d6-b09d-af3a3640bc8c`, SHA-256
  `BF7573ABD07B354142E1A3D7664A6D6C7FC123099EA4C524718C1A1D362CA9E6`;
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
- Reset TEST reale `reset-r05-20260727-t09-final` completato: backup locale,
  backup Registro e backup Limbo verificati; stato locale, `bucoliche`,
  `Virgilio_Inbox`, Limbo e coda Gmail `da-traghettare` sono vuoti. Le tre
  anagrafiche sono rimaste `4/4/13`; configurazione, credenziali e machine ID
  locali sono preservati. Caronte e avvio automatico restano fermi.
- Gate residuo: nessuno. Il collaudatore ha dichiarato `PASS` il 2026-07-28;
  Codex ha soltanto registrato l'esito umano.
- La RC installata `0.11.0-7e18277` contiene T10 e T11 ed e` valida per il
  collaudo focalizzato sul caso MIME reale e sul completamento Gmail.
- `gui`/`gui_*` sono `ABANDONED_LEGACY`; target ammessi: `user_app` e `maintenance_gui`.
- Le RC precedenti non sono valide per il collaudo finale; le evidenze storiche restano in
  `docs/GUI_U_BACKLOG.md`.
- Contesto normale per una run: `AGENTS.md`, questo file e `docs/NEXT_CODEX_TASKS.md`.
