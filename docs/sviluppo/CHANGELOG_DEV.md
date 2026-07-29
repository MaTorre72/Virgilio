# Changelog sviluppo

- 2026-07-29 +02:00 - Riorganizzata fisicamente la documentazione della 1.1:
  al livello `docs/` resta il solo indice; manuale, architettura, modello dati,
  configurazione, manutenzione, comandi, roadmap e documenti Codex sono nelle
  aree `utente`, `tecnica` e `sviluppo`. Rimossi puntatori e archivio
  concorrenti, aggiornati contratti dei percorsi e assorbita la roadmap
  local-first originale nelle fonti correnti. Gli asset grafici correnti
  restano esclusivamente in `icone/`.

- 2026-07-28 +02:00 - Pulizia post-consolidamento: cinque runbook specialistici
  assorbiti in `RUNBOOKS.md`, rimossi archivi e duplicati documentali, mappa
  corrente ridotta a 19 file. Rimossi checkout Codex storici e cache/build
  locali rigenerabili; preservati dati, credenziali e configurazioni operative.
  Le tre branch remote obsolete indicate dall'utente risultavano gia` assenti;
  rimossa la copia locale confluita `connector/local-state-db`.

- 2026-07-28 +02:00 - Chiuso `CONS-H03` e il programma `CONS`: pubblicato
  l'handoff verificabile della release 1.1 e aperta la pull request `#1` da
  `codex/v1.1-development` verso `main`. Branch pubblicata, merge non eseguito;
  revisione e approvazione restano umane.

- 2026-07-28 +02:00 - Chiuso `CONS-H02`: audit finale integrato su 208 file
  tracciati e 44/44 documenti inventariati, senza superfici legacy o segreti
  operativi versionati. Smoke offline `548 passed`; build Caronte e installer
  1.1.0 con smoke build/installer `OK`; tag annotato locale/remoto e metadati
  pubblicati della release coerenti. Successore `CONS-H03`.

- 2026-07-28 +02:00 - Chiuso `CONS-C05`: i 546 test locali sono classificati
  una sola volta come unita` (171), contratti (99) o integrazione offline (276).
  I livelli hanno ingressi separati e vincolanti; lo smoke continua a eseguire
  l'intera suite una sola volta, senza servizi reali.

- 2026-07-28 +02:00 - Chiuso `CONS-C03`: `__main__` e` ridotto al bootstrap;
  `cli.py` contiene costruzione isolata del parser, dispatch e implementazioni
  esistenti. Help, errori, codici di uscita e ingressi conservati; test area CLI
  `173 passed`; smoke locale `543 passed`.

- 2026-07-28 +02:00 - Chiuso `CONS-C02`: classificati tutti i comandi CLI con
  motivazione. L'help principale espone soltanto `init-config`, `doctor` e
  `watch`; gli ingressi e i comandi tecnici necessari restano raggiungibili ma
  interni. Rimosso l'alias di sviluppo senza consumer `local-watch`, mantenendo
  invariato `watch`. Test CLI mirati `64 passed`; smoke locale verde.

- 2026-07-28 +02:00 - Chiuso `CONS-C01`: il package root espone soltanto
  `__version__`, dalla stessa fonte autorevole usata da metadata e build. Le
  riesportazioni operative accidentali sono rimosse; moduli di ingresso e
  import supportati restano invariati e coperti da contratto. Test mirati
  `17 passed`; smoke locale `535 passed`.

- 2026-07-28 +02:00 - Chiuso `CONS-G04`: ritirati due probe standalone storici
  non raggiungibili e due copie congelate della grafica 1.0. Gli asset correnti,
  gli script di sviluppo supportati, build, test, runbook e contratti CLI/import
  restano invariati; i quattro file sono recuperabili dalla storia Git.

- 2026-07-28 +02:00 - Chiuso `CONS-G03`: rimossi i tre moduli sperimentali di
  classificazione AI/LiteLLM e confronto parser, i sei comandi CLI collegati,
  tre test, cinque fixture e il report Docling esclusivi. GUI, pipeline,
  packaging e CLI supportate conservano i contratti; i file restano
  recuperabili dal commit precedente `2481617`.

- 2026-07-28 +02:00 - Chiuso `CONS-G02`: rimossi i sette moduli della GUI
  legacy, i sette test esclusivi e l'alias CLI deprecato `gui`. Gli ingressi
  supportati `user-gui` e `maintenance-gui`, la build e l'installer conservano
  i contratti correnti; i file rimossi restano recuperabili dalla storia Git.

- 2026-07-28 +02:00 - Chiuso `CONS-G01`: inventariati ingressi installati e di
  sviluppo, tutti i dispatch CLI, gli import diretti di GUI utente e
  Manutenzione e i contenuti di wheel, eseguibile e installer. La GUI legacy
  non e` importata dai target supportati; nessuna rimozione o modifica
  funzionale e` stata eseguita. Test packaging mirati `22 passed`; suite locale
  `600 passed`.

- 2026-07-28 +02:00 - Chiuso `CONS-D04`: storia e baseline 1.1 condensate nel
  changelog pubblico e in questo registro cronologico; 17 backlog, roadmap,
  report e guide assorbite sono stati ritirati dal percorso corrente, dopo
  verifica dei link, e restano recuperabili dal commit `45a19f4`. README,
  runbook e puntatori operativi rimandano soltanto a fonti correnti; smoke
  locale `600 passed`.

- 2026-07-28 +02:00 - Chiuso `CONS-D03`: `docs/RUNBOOKS.md` offre percorsi
  brevi e univoci per setup, sviluppo, test, operazioni e release. Le tre fonti
  `MERGE` pertinenti sono assorbite e marcate storiche; nessun deploy o servizio
  reale e` stato eseguito.

- 2026-07-28 +02:00 - Chiuso `CONS-D02`: consolidata l'architettura corrente
  in `docs/ARCHITETTURA_UNIFICATA.md`, con confini univoci tra profili,
  risorse condivise, GUI utente, Manutenzione, CLI, servizi e GAS. Le quattro
  fonti architetturali `MERGE` sono marcate storiche e non concorrenti.

- 2026-07-28 +02:00 - Chiuso `CONS-D01`: inventariati una sola volta tutti i
  59 documenti versionati in `docs/DOCUMENT_INVENTORY.md`, usando esclusivamente
  `KEEP`, `MERGE`, `HISTORY` e `REMOVE`; destinazioni e motivazioni obbligatorie
  sono esplicite e fonti operative, report datati e archivio sono distinguibili.

- 2026-07-28 +02:00 - Chiuso `CONS-R04`: creato e pubblicato il tag annotato
  `v1.1.0` sul commit sorgente release `68f3b90`; annotazione con installer,
  SHA-256 e Build ID e riferimenti locale/remoto verificati coincidenti.

- 2026-07-28 +02:00 - Chiuso `CONS-R03`: prodotta dal commit pulito `68f3b90`
  la release desktop `CaronteSetup-1.1.0-68f3b90.exe` (30.699.894 byte),
  SHA-256 `8CD723E3DF14DFB30DE1E17D5BDDC29C81E3C87558DCBC85CA33828AE40DDE92`,
  Build ID `8268f442-8066-45c3-a9bc-0b32f6acdc76`. Manifest e OAuth inclusi;
  build e smoke installer `PASS`, dati utente preservati.

- 2026-07-28 +02:00 - Chiuso `CONS-R01`: versione prodotto corrente `1.1.0`;
  package metadata, runtime e build leggono l'unica fonte autorevole
  `virgilio_connector._version.__version__`, con `VERSION` come marcatore
  verificato. Informazioni e `--build-info` coperti dai mirati `22 passed`;
  smoke locale `600 passed`. Nessun cambiamento funzionale o build reale.

- 2026-07-28 +02:00 - Avviato il programma autonomo `CONS` successivo al
  collaudo finale: 20 task seriali per release `1.1.0`, consolidamento
  documentale, pulizia, refactor e handoff. Formalizzati fetch/pull fast-forward,
  commit e push non forzato, cadenza oraria, contesto minimo e monitoraggio token
  senza stime quando il dato di piattaforma non e` esposto. Primo task
  `CONS-R01`; `main`, merge e servizi reali restano esclusi. Smoke di governance
  verde: `599 passed`, `smoke_local_connector: OK`.

- 2026-07-28 +02:00 - `PASS` umano esplicito sul collaudo finale della RC
  `CaronteSetup-0.11.0-7e18277.exe`: chiusi `GUI-U-R05`, il recupero prodotto e
  `GATE U-H3`. I precedenti `FAIL` restano conservati come storico; nessun esito
  e` stato dedotto o approvato da Codex.

- 2026-07-28 +02:00 - Distribuita la RC T11
  `CaronteSetup-0.11.0-7e18277.exe`, Build ID
  `04736b60-fca3-49d6-b09d-af3a3640bc8c`, SHA-256
  `BF7573ABD07B354142E1A3D7664A6D6C7FC123099EA4C524718C1A1D362CA9E6`.
  Build e smoke installer `PASS`; payload installato, registrazione, collegamenti
  e preservazione esatta di configurazione/database verificati. Caronte lasciato
  fermo; Apps Script, Gmail e stato TEST invariati.

- 2026-07-28 +02:00 - Completato `GUI-U-R05-T11`: estrazione ricorsiva degli
  allegati nominati o espliciti anche in `multipart/alternative ->
  multipart/mixed`, riuso dell'identita` IMAP tra scanner/processor e cicli,
  warning operativo per mail trovate senza allegati acquisibili. Mirati
  `132 passed`; suite e smoke `599 passed`. Solo fixture sintetiche; Gmail,
  Google, Apps Script e RC installata invariati.

- 2026-07-27 +02:00 - Distribuita la RC T10
  `CaronteSetup-0.11.0-e9e0949.exe`, Build ID
  `11924c13-22c8-4a0c-ab59-20faf2751d75`, SHA-256
  `CA87D016EA122EA8A3B5091A01FA7339839146808FE57DAEEBC427381FD14AB6`.
  Build e smoke installer `PASS`; identita` payload, registrazione, collegamenti
  e preservazione dati verificati. Apps Script e reset invariati.

- 2026-07-27 +02:00 - Completato `GUI-U-R05-T10`: il follow-up riprende soltanto
  staged/handoff/completion fino alla chiusura o alla pausa; Gmail rimuove la
  label di ingresso dalla cartella destinazione usando `X-GM-MSGID`, senza
  `DELETE`, `MOVE` o `EXPUNGE`. Caso reale: quattro mail `completed`, coda
  `da-traghettare` vuota. Mirati `146 passed`; suite e smoke `595 passed`.
  Apps Script invariato; nuova RC ancora da generare.

- 2026-07-27 +02:00 - Completato il reset totale TEST
  `reset-r05-20260727-t09-final`: backup locale/Registro/Limbo verificati; stato
  locale, `bucoliche`, `Virgilio_Inbox`, Limbo e coda Gmail `da-traghettare`
  vuoti. Le quattro vecchie mail sono state rimosse soltanto dall'etichetta di
  ingresso. Anagrafiche `4/4/13`, configurazione, credenziali e machine ID
  preservati; Caronte e avvio automatico fermi.

- 2026-07-27 +02:00 - Distribuita la RC del correttivo `GUI-U-R05-T09`:
  `CaronteSetup-0.11.0-1f0e6e8.exe`, Build ID
  `a0bb673d-6d1d-417f-9d26-cb8d5de71600`, SHA-256
  `5A2405EC861F2CE3654C0CF01D32857FEB496A8218042FC715CE6832C515E5D2`.
  Build e smoke installer `PASS`; identita` del payload installato, collegamenti,
  registrazione e preservazione dei dati verificati. Apps Script invariato; reset
  TEST non eseguito.

- 2026-07-27 +02:00 - Completato `GUI-U-R05-T09`: verifica Limbo con retry a
  backoff e timeout globale, ripresa degli staged `waiting`, completion-only per
  10 minuti dopo il controllo manuale, una riga Bucoliche locale per documento e
  UIDVALIDITY letto una volta per sessione. Suite e smoke `593 passed`; nessuna
  pubblicazione, installazione, modifica Gmail o reset reale.

- 2026-07-27 +02:00 - Distribuito `GUI-U-R05-T08`: Apps Script versione `40`
  sul deployment esistente; RC `CaronteSetup-0.11.0-60cc6ff.exe` installata
  (Build ID `b93b7fa7-60ca-462f-9ae7-1e7dc7cae0f6`). Ripristinate e verificate
  le tre anagrafiche; reset `reset-r05-20260727-t08-final` completato con backup,
  dati operativi vuoti e anagrafiche invariate. Smoke finale `589 passed`.

- 2026-07-27 +02:00 - Completato `GUI-U-R05-T08`: completion vincolata allo
  stato finale `archiviato`, post-condizioni Gmail verificate, anagrafiche
  canoniche preservate e ripristino esplicito da backup senza dati fittizi.
  Mirati `107 passed`; regressione e smoke `587 passed`; nessuna azione live.

- 2026-07-25 +02:00 - Completato `GUI-U-R04-R06`: release candidate locale
  con build e installer autonomi, manifest release SHA-256/commit/build ID e
  flag verificabile `oauth_client_included`; risorsa OAuth inclusa e hash
  confrontato. `clasp 3.3.0 status` e` coerente con i soli file Apps Script
  attesi, senza push, pull o deploy. Test build/installer `13 passed`; build e
  smoke installer `PASS`. La checklist umana riprova esclusivamente
  notifica/link, fasi/conteggi e lessico. Stato successivo:
  `WAITING_HUMAN_REVIEW` per pubblicazione Apps Script autorizzata e pilota.

- 2026-07-25 +02:00 - Completato `GUI-U-R04-R05`: Caronte non mostra piu`
  `Cartella completati` nel percorso ordinario, perche` il completamento IMAP
  resta disabilitato. Il valore storico viene preservato internamente durante
  modifica e riapertura e le nuove caselle ricevono soltanto il default
  interno; nessuna scrittura IMAP e` stata attivata. Attivita distingue ora
  documento acquisito, lavoro disponibile in Virgilio e pratica archiviata.
  Mirati fake `44 passed`, regressione IMAP read-only inclusa; smoke locale
  `550 passed`, senza rete o credenziali reali.

- 2026-07-25 +02:00 - Completato `GUI-U-R04-R03` dopo il `FAIL` umano
  della RC `bab6e92`: la presa in carico genera un link `/exec` assoluto
  correlato all'`inbox_id` e lo restituisce al connector insieme allo stato
  della notifica. Chat e Telegram ricevono, quando configurati, un messaggio
  leggibile con documento, provenienza e azione `Apri in Virgilio`; il retry
  riusa la riga e non reinvia un esito gia` `sent`, mentre un problema resta
  riprovabile. Il contratto resta metadata-only e il connector blocca il
  completamento se manca il link o lo stato osservabile. Harness Apps Script
  puro `OK`, test fake Python `25 passed`, smoke locale `545 passed`; nessuna
  rete reale, push o deploy.

- 2026-07-25 +02:00 - Completato `GUI-U-R04-R02` dopo `FAIL` umano della
  RC `24d54be`: il Registro usava ancora file OAuth della CLI e non veniva
  aggiornato dalla pipeline Home. Il nuovo servizio usa il client Desktop
  incluso con scope Sheets, apre il browser e conserva/rinnova l'autorizzazione
  nel Gestore credenziali Windows. Un Registro selezionato viene abilitato
  automaticamente e, dopo il consenso, Caronte crea sezioni/intestazioni
  mancanti senza sovrascrivere strutture incompatibili. La pipeline compone
  `handoff -> registry -> completion`; un errore Registro lascia il messaggio
  riprovabile. Il pulsante Manutenzione resta sempre disponibile. Mirati
  `72 passed`, smoke finale `540 passed`; una prima esecuzione aveva raggiunto
  `539 passed` prima dell'errore intermittente `init.tcl`, non riprodotto.

- 2026-07-24 +02:00 - Completato `GUI-U-R04-R01` dopo `FAIL` umano UX
  della RC `0d46d69`: la pagina utente non espone piu` URL, codici o richieste
  amministrative senza percorso. Mostra soltanto la prontezza di Registro e
  consegna e apre Caronte Manutenzione. La presentazione separata spiega e
  salva il foglio Registro, l'indirizzo `/exec` ottenuto da `Gestisci
  deployment` e `VIRGILIO_TOKEN` dalle proprieta` dello script, proteggendo la
  chiave in Windows e mantenendola se il campo resta vuoto. L'installer crea
  accessi Start distinti a Caronte e Caronte Manutenzione e lo smoke apre
  entrambe le finestre. Mirati `35 passed`, Tk isolato `1 passed`, smoke locale
  `532 passed`; stabilizzato il controllo Tk che ereditava la scala della
  schermata precedente.

- 2026-07-24 +02:00 - Preparata `GUI-U-R04` come
  `WAITING_HUMAN_REVIEW`: costruita la release candidate
  `CaronteSetup-0.11.0-0d46d69.exe` dal commit
  `0d46d69ea3eeb271362b7d2ee61e5184136afd98`, Build ID
  `fb8018c0-b473-4035-9370-32877a32f72a`, SHA-256
  `E920DE1248DB5338581C25B54BFE13D9DD7DA74110613E885EA6F74B6AF34D62`.
  Il client OAuth Google locale e` incluso su autorizzazione esplicita
  dell'utente; manifest e release manifest coincidono, build e smoke installer
  sono `PASS`. Predisposto il fascicolo umano identificato; il gate non e`
  approvato automaticamente. La disinstallazione standard Windows e` in scope,
  l'avvio diretto del disinstallatore resta a priorita` molto bassa.

- 2026-07-24 +02:00 - Completato `GUI-U-R03-R06`: la pipeline operativa
  compone i client CLI esistenti `verify-drive-staging` e
  `intake-da-archiviare` tra copia nel Limbo e completamento IMAP. Gli ID Drive
  gia` restituiti da Apps Script vengono conservati e validati; attesa cloud,
  errori e rifiuti non completano il messaggio, mentre retry e intake
  idempotente non duplicano la presa in carico. Attivita espone consegna,
  sincronizzazione e problema in termini utente. Audit pre-RC: eliminata la
  dipendenza residua dal `.env` di sviluppo; `Registro e avvio` salva
  l'indirizzo e protegge il codice nel Gestore credenziali Windows, e i worker
  installati recuperano autonomamente anche le credenziali delle caselle.
  Mirati finali `92 passed`, Tk reale `1 passed`, smoke locale `529 passed`;
  una prima esecuzione aveva raggiunto `528 passed` prima di un errore
  transitorio Tcl/Tk preesistente, non riprodotto a toolchain libera.

- 2026-07-24 +02:00 - Priorita` riallineata per decisione utente: il
  disinstallatore diretto e` rinviato alla fine con priorita` molto bassa.
  Diagnosi read-only del percorso reale: la pipeline Home copia nel Limbo ma
  non compone verifica Drive e presa in carico in `Da archiviare`; Apps Script
  restituisce gia` gli ID necessari, oggi scartati dal client Python. Proposto
  il task finito `GUI-U-R03-R06 - Consegna operativa a Da archiviare`.

- 2026-07-24 +02:00 - Completato `GUI-U-R03-R05`: i campi Limbo del primo
  avvio e di Impostazioni e le tre cartelle operative avanzate usano una
  larghezza condivisa di 48 caratteri e colonne elastiche. Percorsi lunghi,
  selezione, scorrimento, copia e incolla restano disponibili; layout entro
  960x640 a 100%/125%. Regressione rossa acquisita, gruppo mirato finale
  `47 passed`, smoke locale `506 passed`.

- 2026-07-24 +02:00 - Chiuso `GUI-U-R03 = DONE` con conferma umana
  `H-R03-01 = PASS`: selezione, validazione, salvataggio, ritorno, riapertura,
  persistenza e modifica del Limbo approvati. `H-R03-01`--`H-R03-06 = PASS`
  e `R03-AC1`--`R03-AC5 = MET`. Osservazione non bloccante: i campi che
  mostrano percorsi cartella sono troppo piccoli; proposto
  `GUI-U-R03-R05 - Campi cartella leggibili`, in attesa di approvazione.

- 2026-07-24 +02:00 - Ripresa umana `GUI-U-R03` sulla build R03-R04
  `eaf05fd`, ID `0c40a31d-ee7a-4d8c-9f0d-5ff795fb5b39`: conferma esplicita
  `H-R03-06 = PASS`. Nessun UAC o finestra tecnica; attivazione, stato,
  persistenza dopo riapertura e nuovo accesso Windows, disattivazione e
  persistenza dello stato non attivo tutti approvati. `R03-AC5 = MET`; resta
  soltanto `H-R03-01`, non ancora registrato.

- 2026-07-24 +02:00 - Completato `GUI-U-R03-R04`: il controllo automatico
  usa `Run` per il solo utente corrente e avvia il worker congelato con
  configurazione e intervallo installati, senza Task Scheduler, UAC o
  amministratore. Registro e avvio restano indipendenti; disinstallazione
  pulisce registrazione nuova e task legacy. Mirati `27 passed`, smoke locale
  `504 passed`; build e installer identificati con smoke `PASS`.

- 2026-07-24 +02:00 - `H-R03-06 = FAIL` umano sulla build `8241325`:
  `Attivazione non riuscita. Riprova da Windows.` e nessuna attivita
  `Caronte - controllo automatico` creata. Diagnosi read-only: il gateway usa
  `schtasks` dalla GUI ordinaria; il Registro non configurato nella stessa
  schermata e` un prerequisito separato. Proposto `GUI-U-R03-R04`, senza
  modifiche di codice in attesa di approvazione.

- 2026-07-24 +02:00 - Prosecuzione umana `GUI-U-R03`: conferma esplicita
  `H-R03-05 = PASS` sulla build `8241325`. Riduzione a icona, chiusura,
  riapertura, persistenza, stato e assenza di processi duplicati sono stati
  approvati; `R03-AC4 = MET` e il collaudo prosegue da `H-R03-06`.

- 2026-07-24 +02:00 - Prosecuzione umana `GUI-U-R03`: conferma esplicita
  `H-R03-04 = PASS` sulla build `8241325`, con tre screenshot di Controlla ora,
  avvio, pausa e Attivita. La verifica casella e` correttamente integrata nel
  collegamento gia` approvato e non e` un pulsante separato. `R03-AC3 = MET`;
  il collaudo prosegue da `H-R03-05`.

- 2026-07-24 +02:00 - Prosecuzione umana `GUI-U-R03` sulla build `8241325`,
  ID `7dcae8b2-5bd2-47b6-9c89-f53b4cf4c1ff`: conferma esplicita
  `H-R03-03 = PASS`. Con `H-R03-02` gia` approvato, `R03-AC2 = MET`; il
  collaudo prosegue senza ripetizioni da `H-R03-04`.

- 2026-07-24 +02:00 - Ripresa umana `GUI-U-R03` sulla build `8241325`,
  ID `7dcae8b2-5bd2-47b6-9c89-f53b4cf4c1ff`: conferma esplicita
  `H-R03-02 = PASS` dopo reinstallazione. I `FAIL` precedenti restano storici;
  il collaudo prosegue senza ripetizioni da `H-R03-03`.

- 2026-07-24 +02:00 - Prodotta la build operativa R03-R03 identificata
  `CaronteSetup-0.11.0-8241325.exe`, commit
  `8241325bf96d858259a577c87ffaba8c25513a05`, Build ID
  `7dcae8b2-5bd2-47b6-9c89-f53b4cf4c1ff`, SHA-256
  `79BC5677B21B29CAF3F7E07A9394072FBBBA446DA573FF5AF0181B8CFF260FF8`.
  Client OAuth Desktop incorporato; smoke build e installer `PASS`. Fascicolo
  locale ignorato pronto; `H-R03-02` resta `FAIL` fino alla ripresa umana.

- 2026-07-24 +02:00 - Completato `GUI-U-R03-R03`: Google usa una sola azione
  per autorizzare, verificare e salvare; IMAP usa `Verifica e aggiungi`.
  Credenziali orfane riconciliate con rollback, errori resi visibili senza
  dettagli sensibili e rimosso il conteggio ambiguo del campione. Rosso
  acquisito `6 failed, 16 passed`; verde core `37 passed`, Tk `1 passed`.
  Smoke locale finale `501 passed`. Nuova build rinviata alla run successiva.

- 2026-07-24 +02:00 - Seconda ripresa umana `GUI-U-R03`, build `bb9b16e`,
  ID `9337fa8d-737e-4b16-8f82-b68cb129c778`: OAuth e verifica `INBOX`
  riescono, ma `Aggiungi casella` non salva e non mostra errore. Diagnosi
  read-only: configurazione assente e riferimenti protetti residui incompatibili
  con il salvataggio create-only; `25 messaggi` e` il limite del campione.
  Registrata anche la richiesta di semplificare il flusso; proposto R03-R03.

- 2026-07-24 +02:00 - Completato `GUI-U-R03-R02`: Caselle espone nelle
  impostazioni avanzate le cartelle da controllare, completati e problemi,
  obbligatorie, modificabili e persistenti per account. Il caso reale
  `da-traghettare` senza cartella madre e` verde; il check resta su `INBOX`.
  Core mirato `17 passed`, sola prova Tk interessata `1 passed` a
  960x640/100%/125%. Nuova build rinviata alla run successiva.

- 2026-07-24 +02:00 - Completato `GUI-U-R03-R01`: la verifica collegamento
  dichiara e usa `INBOX`, senza dipendere dalla cartella operativa assente;
  regressione prima rossa e poi verde, gruppo mirato R03-R01/R03-T02
  `15 passed`. Nessuna rete o credenziale reale nei test. Emerso separatamente
  che la GUI salva cartelle operative implicite diverse dal caso reale
  `da-traghettare`; proposto R03-R02 e rinviata la nuova build.

- 2026-07-24 +02:00 - Collaudo umano `GUI-U-R03` interrotto con `FAIL` su
  `H-R03-02`: OAuth interno completa, ma la GUI non aggiunge la prima casella.
  La diagnosi read-only ha escluso rete e policy Google e ha riprodotto
  `SELECT READ-ONLY failed` sulla cartella implicita `Virgilio/da-traghettare`;
  `INBOX`, ricerca e lettura di 100 messaggi riescono. Proposto, in attesa di
  approvazione, `GUI-U-R03-R01 - Verifica collegamento su INBOX`.

- 2026-07-24 +02:00 - Completato `GUI-U-R03-T03`: il percorso reale conserva
  Limbo e caselle attraverso Benvenuto -> Limbo -> Caselle -> Riepilogo ->
  Home; il Riepilogo mostra stati/correzioni e `Completa configurazione`.
  Una prova Tk reale ha rilevato un Riepilogo di 971 px a 125%, corretto con
  wrapping dei dettagli; gruppo mirato finale `39 passed`, smoke locale `494 passed`. Prossimo task:
  collaudo umano unico `GUI-U-R03` sulla build operativa.

- 2026-07-24 +02:00 - Completato `GUI-U-R03-T02`: ripristinata l'esecuzione
  del runtime fuori dal sandbox e le due prove mirate, con base temporanea
  isolata, hanno coperto seconda casella, credenziali distinte, CRUD,
  persistenza e verifica asincrona (`12 passed`). Nessun codice applicativo
  modificato; prossimo task `GUI-U-R03-T03`.

- 2026-07-24 +02:00 - `GUI-U-R03-T02` bloccato prima di modifiche: il runtime
  obbligatorio `local_connector\.venv\Scripts\python.exe` restituisce `Accesso
  negato` prima di avviare le due prove mirate. Nessun codice e nessun criterio
  sono stati modificati; unica azione necessaria: ripristinare il runtime e
  rieseguire solo quelle prove.

- 2026-07-23 +02:00 - Chiarita la continuita` R02 -> R03: il demo R02 e`
  `SUPERSEDED_BY_R3`, mentre tutti gli otto requisiti UX R2 restano vincolanti
  sul prodotto reale. Aggiunte matrice di trasferimento, `GUI-U-R03-T03` per
  percorso completo/Riepilogo/Home e regola di un solo collaudo umano R3.

- 2026-07-23 +02:00 - Completato `GUI-U-R03-T01`: la scelta Posta IMAP
  rimuove l'host Google implicito, mostra subito password e parametri server,
  salva la prima casella tramite il servizio condiviso e apre Home con l'azione
  `Completa configurazione`. Nuova prova mirata `1 passed`; evidenze precedenti
  mantenute senza ripetere suite, smoke o collaudi.

- 2026-07-23 +02:00 - Su decisione utente, il recupero GUI passa dal prototipo R02 non accettato al percorso operativo reale: dati demo solo per evidenze interne, avvio di `GUI-U-R03-T01` per configurare e salvare la prima casella IMAP senza dipendere da Google.

- 2026-07-23 +02:00 - Collaudo umano `GUI-U-R02` registrato `FAIL` su installazione pulita: dopo Limbo, Caselle non consente di inserire le caselle demo e blocca Riepilogo/Home; la build installata presenta il percorso ordinario non configurato, mentre R02 richiede un demo completo e isolato senza Google. Osservata anche la difformita` `Termina configurazione` rispetto a `Completa configurazione`. Proposti i correttivi finiti `GUI-U-R02-R01` e `GUI-U-R02-R02`, da approvare prima di modificare codice.

- 2026-07-21 - Completato `GUI-U-R02-T03`: Home dimostrativa ora mostra stato,
  caselle, prossima azione, attivita`, problemi e azione primaria con dati solo
  in memoria; l'eseguibile supporta il percorso demo isolato per le prove.
  Build e installer puliti `4cbcea4` con build ID
  `f7eb037d-924e-4a04-b9a9-3f2751137a42` hanno superato gli smoke e il fascicolo
  ignorato contiene manifest, hash e dieci screenshot diretti della build
  installata. Test mirati `33 passed`, suite `492 passed`, smoke `491 passed`.
  `GUI-U-R02` e` ora `WAITING_HUMAN_REVIEW`; Codex non dichiara `PASS`.

- 2026-07-21 - Completato `GUI-U-R02-T02`: ripristinata la venv locale da
  Python Windows 3.13.14 con Tcl/Tk 8.6.15; Benvenuto, Limbo, Caselle e
  Riepilogo espongono gerarchia e azioni coerenti, mentre Caselle rientra a
  960x640 anche a scala 125%. Aggiunto test Tk reale delle quattro schermate;
  test GUI mirati `31 passed`, suite e smoke `489 passed`. Prossimo task
  `GUI-U-R02-T03 - Home dimostrativa ed evidenze installate`.

- 2026-07-21 - `GUI-U-R02-T02` bloccato prima delle modifiche: il runtime di
  test non inizializza Tcl/Tk (`init.tcl` assente) e la venv di build non avvia
  Python (`Accesso negato`), quindi non sono producibili le screenshot e le
  prove di resize obbligatorie. Il codice parziale e` stato annullato; unica
  azione necessaria: ripristinare un runtime Python Windows eseguibile con
  Tcl/Tk completo e rieseguire il task dall'inizio.

- 2026-07-20 - Completato `GUI-U-R02-T01`: introdotto un percorso demo
  esclusivamente in memoria attraverso Benvenuto, Limbo, Caselle, Riepilogo e
  Home, con Limbo e due caselle sintetiche coerenti nel ritorno. Nessun adapter
  di configurazione, credenziali, rete o salvataggio viene interrogato; test
  mirati `22 passed`, suite e smoke locale `488 passed`. Prossimo task
  `GUI-U-R02-T02 - Schermate del primo avvio osservabili`.

- 2026-07-20 - Suddiviso `GUI-U-R02` nel percorso dimostrativo isolato, nelle
  schermate del primo avvio e nelle evidenze installate: ogni task possiede
  criteri binari, prove, confini e blocco; il primo task eseguibile e`
  `GUI-U-R02-T01`.

- 2026-07-20 - Completato `GUI-U-R01`: manifest interno validato, `Caronte.exe --build-info`, finestra `Informazioni su Caronte`, build di collaudo con gate Git, installer nominato con versione/commit, manifest release SHA-256 e smoke installato con confronto di versione/commit/build ID. Creato `docs/GUI_U_HUMAN_ACCEPTANCE.md`; `GUI-U-E3-T07` - `T14` riclassificati `IMPLEMENTED_NOT_ACCEPTED`; suite e smoke locale `487 passed`. Prossimo task `GUI-U-R02 - Prototipo visuale completo`, con esito terminale obbligatorio `WAITING_HUMAN_REVIEW`.

- 2026-07-20 - `GATE U-H3 = FAIL`: il collaudo umano non ha rilevato alcun miglioramento concreto rispetto alle osservazioni precedenti; nessuna correzione e` stata validata nel percorso percepito. `GUI-U` e` posta `BLOCKED`; nessun altro correttivo autonomo e` autorizzato prima di un nuovo piano di recupero con scenari osservabili e criteri di accettazione umani.

- 2026-07-20 - Completato `GUI-U-E3-T14`: `Registro e avvio` resta nella finestra Caronte, guida lo stato del Registro e del collegamento Google senza dettagli tecnici e presenta una sola azione per il controllo automatico; i comandi del pianificatore Windows non aprono una console. Test mirati `18 passed`, suite local connector e smoke `478 passed`; inventario stringhe vietate, diff e scansione segreti verificati. Prossimo passo `GATE U-H3 - Collaudo umano di distribuzione`.

- 2026-07-20 - Completato `GUI-U-E3-T13`: ogni controllo della Home lascia un riscontro leggibile nella sorgente condivisa di `Attivita e problemi`, inclusi avvio, pausa, completamento e controllo senza nuovi documenti; i dettagli tecnici restano chiusi senza una riga selezionata. Test mirati `18 passed`, suite local connector e smoke `475 passed`; inventario stringhe vietate, diff e scansione segreti verificati. Prossimo task `GUI-U-E3-T14 - Registro e avvio guidati senza finestre tecniche`.

- 2026-07-20 - Completato `GUI-U-E3-T12`: la chiusura dalla barra del titolo puo` ridurre Caronte a icona secondo una preferenza persistita e ricaricata; i controlli distinguono `Riduci a icona`, ritorno alla Home e `Chiudi Caronte`, che arresta il supervisore posseduto. Test mirati `31 passed`, suite local connector e smoke locale `474 passed`; inventario stringhe vietate, diff e scansione segreti verdi. Prossimo task `GUI-U-E3-T13 - Attivita` visibili e utili`.

- 2026-07-20 - Completato `GUI-U-E3-T11`: l'avvio automatico usa nella distribuzione installata `Caronte.exe` sia per l'accesso Windows sia per il controllo automatico, senza repository o runtime di sviluppo; rimozione e disinstallazione arrestano prima il controllo e cancellano le integrazioni di avvio. Test mirati `29 passed`, suite e smoke locale `472 passed`, build autonoma, avvio dalla sola cartella copiata e smoke installer isolato verdi. Prossimo task `GUI-U-E3-T12 - Chiusura e riduzione a icona comprensibili`.

- 2026-07-20 - Suddiviso il completamento dopo il collaudo anticipato: `GUI-U-E3-T11` torna avviabile dopo il ripristino della build; aggiunti `T12` (chiusura/riduzione), `T13` (Attivita`) e `T14` (Registro e avvio), con criteri binari e prove dedicate. `GATE U-H3` resta bloccato finche` tutti i task `T07` - `T14` non sono `DONE`.

- 2026-07-17 - `GUI-U-E3-T11` bloccato: i test mirati (`34 passed`), suite e smoke locale (`471 passed`) hanno validato le prove sintetiche, ma il build gate necessario allo smoke installazione/attivazione/disinstallazione fallisce prima di PyInstaller. La `.venv` e tutte le toolchain locali di build gia` predisposte non inizializzano Tcl/Tk (`init.tcl` non utilizzabile), percio` non e` possibile produrre `Caronte.exe` aggiornato senza ripristinare la toolchain. Le modifiche parziali sono state annullate; unica azione necessaria: ripristinare una toolchain Python Windows completa con Tcl/Tk funzionante e rieseguire T11 dall'inizio.

- 2026-07-17 - Completato `GUI-U-E3-T10`: il Registro e` sempre attivo nella GUI utente e non espone Bucoliche o dettagli tecnici; l'utente collega solo Google e riceve esiti leggibili, mentre l'amministratore sceglie per ogni installazione il foglio condiviso nella nuova presentazione `Caronte Manutenzione`. Caronte persiste il solo identificativo stabile del foglio, quindi un cambio della cartella madre non richiede riconfigurazione. Test mirati `14 passed`, regressione `49 passed`, suite local connector e smoke `467 passed`; inventario stringhe vietate, diff e scansione segreti verdi. Prossimo task `GUI-U-E3-T11 - Avvio automatico della distribuzione installata`.

- 2026-07-17 - Completato `GUI-U-E3-T09`: Gmail/Workspace usa il flusso OAuth Desktop ufficiale con browser e callback locale, la GUI non offre password Google, IMAP autentica con XOAUTH2, token e rinnovi restano nel gestore credenziali e gli esiti distinguono configurazione incompleta, rifiuto e rete assente; IMAP generico resta invariato. La build accetta e incorpora il client centrale come input locale ignorato. Test mirati `51 passed`, suite local connector e smoke `464 passed`; inventario stringhe vietate, diff e scansione segreti verdi. Prossimo task `GUI-U-E3-T10 - Registro e collegamento Google comprensibili`.

- 2026-07-17 - Completato `GUI-U-E3-T08`: il wizard identifica senza ambiguita` la cartella locale del Limbo Drive sincronizzato, wizard e Impostazioni usano un selettore di directory assolute esistenti e conservano il percorso tra navigazione, riapertura e salvataggio; i controlli testuali condividono selezione, copia/incolla e menu contestuale Windows. Test mirati `43 passed`, suite local connector e smoke `454 passed`; inventario stringhe vietate, diff e scansione segreti verdi. Prossimo task `GUI-U-E3-T09 - Accesso alle caselle Google`.

- 2026-07-17 - Completato `GUI-U-E3-T07`: verifica casella asincrona con riscontro immediato ed errori azionabili redatti; la Home consuma periodicamente gli eventi condivisi e distingue accettazione, avanzamento, completamento, doppio avvio e pausa aggiornando stato, ultimo controllo e attivita`. Test mirati `40 passed`, suite local connector e smoke `448 passed`; scansioni stringhe vietate e segreti verdi. Prossimo task `GUI-U-E3-T08 - Limbo, persistenza e interazioni di base`.

- 2026-07-17 - `GATE U-H3 = FAIL` su collaudo umano: installazione, collegamento Start, conclusione wizard, persistenza e disinstallazione riusciti; falliti i riscontri osservabili di verifica/controllo/avvio/pausa, la chiarezza e persistenza del Limbo, l'accesso Gmail, il percorso Registro/Google, l'avvio automatico e le interazioni di copia/incolla. Suddivise le correzioni finite in `GUI-U-E3-T07` - `GUI-U-E3-T11`; corrente `GUI-U-E3-T07`, gate in `WAITING_FOR_PREVIOUS_TASKS`.

- 2026-07-17 - Completato `GUI-U-E3-T06`: aggiunto `CaronteSetup.exe` per installazione per utente senza privilegi, collegamento Start, registrazione di disinstallazione HKCU, rimozione del programma con conservazione di configurazione e dati, build e smoke isolato del primo avvio. Test task `9 passed`, suite e smoke locale `442 passed`, smoke installer verde con riferimenti Python rimossi. `GATE U-H3 = WAITING_HUMAN_REVIEW` e richiede esito umano esplicito.

- 2026-07-17 - Completato `GUI-U-E3-T05`: aggiunte build PyInstaller one-folder deterministica, entry point `Caronte.exe`, dipendenze runtime Windows dichiarate, script di build e smoke isolato e documentazione operativa. Due build pulite identiche (`1582` file, zero differenze SHA-256) e avvio dalla sola cartella copiata con titolo `Caronte`; test task (`10 passed`), suite local connector e smoke (`438 passed`) verdi. Prossimo task `GUI-U-E3-T06 - Installer Windows`.

- 2026-07-17 - Completato `GUI-U-E3-T04`: sostituita la riesportazione legacy con la nuova presentazione indipendente `Caronte Manutenzione` e aggiunto un servizio applicativo condiviso per backup locale, verifica integrita`, report diagnostico redatto e reset protetto da conferma e backup automatico. Test task (`50 passed`), suite local connector e smoke (`433 passed`) verdi; scansioni import legacy e segreti verdi. Prossimo task `GUI-U-E3-T05 - Build autonoma`.

- 2026-07-16 - Completato `GUI-U-E3-T03`: aggiunti servizio applicativo e percorso guidato utente per attivare/disattivare Bucoliche, collegare Google, verificare il registro in sola lettura e installare/rimuovere il controllo automatico tramite adapter Task Scheduler iniettabile; stati ed errori noti sono tradotti senza dettagli tecnici. Test task (`28 passed`), suite local connector e smoke (`428 passed`) verdi; scansioni stringhe vietate, import legacy e segreti verdi. Prossimo task `GUI-U-E3-T04 - Manutenzione avanzata`.

- 2026-07-16 - Completato `GUI-U-E3-T02`: la GUI utente espone impostazioni ordinarie per cartella Limbo, intervallo di controllo, avvio automatico su Windows e comportamento alla chiusura, tutte persistite nel modello condiviso; l'integrazione di avvio usa un adapter Windows iniettabile e la chiusura mantiene l'arresto esplicito del worker. Test task (`8 passed`), regressione mirata (`30 passed`), suite local connector e smoke (`422 passed`) verdi; scansioni stringhe vietate e segreti verdi. Prossimo task `GUI-U-E3-T03 - Bucoliche e avvio Windows`.

- 2026-07-16 - Completato `GUI-U-E3-T01`: la GUI utente espone una tabella `Attivita e problemi` alimentata dalla proiezione sicura degli eventi locali esistenti, con filtri combinabili per casella, esito e data, azioni consigliate per errori e conflitti e dettagli tecnici separati e chiusi per default. Test task/regressione GUI (`27 passed`), suite local connector e smoke (`414 passed`) verdi; nessun import della presentazione legacy e nessun dato reale usato. Prossimo task `GUI-U-E3-T02 - Impostazioni essenziali`.

- 2026-07-16 - `GATE U-H2 = PASS` su conferma umana esplicita dopo le correzioni di `GUI-U-E2-T07`: il percorso verticale e` approvato, la sotto-epica E3 e` sbloccata e il prossimo task univoco e` `GUI-U-E3-T01 - Attivita` e problemi`. Smoke locale verde (`409 passed`); nessun codice applicativo modificato.

- 2026-07-16 - Completato `GUI-U-E2-T07`: `Casella attiva` mostra e salva uno stato binario coerente; il wizard termina esplicitamente sulla Home nella stessa sessione; `Impostazioni` riapre valori e credenziali esistenti per la modifica; riduzione a icona e chiusura sono visibili e la chiusura arresta il worker. Test T07 (`5 passed`), regressione GUI utente (`36 passed`), suite local connector e smoke (`409 passed`) verdi; inventario testi privo di termini tecnici e viste legacy. `GATE U-H2` e` di nuovo `WAITING_HUMAN_REVIEW` e Codex non ne dichiara il `PASS`.

- 2026-07-16 - `GATE U-H2 = FAIL` su collaudo umano: confermati il funzionamento del percorso principale e l'assenza di termini tecnici o percorsi del repository; rilevati stato `Casella attiva` indeterminato e invertito, mancanza della conclusione esplicita del wizard verso la Home, assenza di accesso dalla Home per rivedere la configurazione e controlli finestra non chiaramente disponibili. Aperto il solo task correttivo `GUI-U-E2-T07`; E3 resta bloccata fino a correzione e nuovo `PASS` umano.

- 2026-07-16 - Completato `GUI-U-E2-T06`: le azioni Home usano un controller applicativo e un runner condiviso in background per controllo singolo, avvio continuo, pausa, rifiuto del doppio avvio e arresto deterministico alla chiusura; la GUI utente non importa moduli legacy. Test task (`32 passed`), suite local connector e smoke (`404 passed`) verdi; una prima esecuzione smoke ha incontrato il noto test Bucoliche fluttuante, poi verde isolato e nella ripetizione completa. `GATE U-H2` e` ora `WAITING_HUMAN_REVIEW` e blocca E3 fino a esito umano esplicito.

- 2026-07-16 - Completato `GUI-U-E2-T05`: la Home utente mostra stato generale, numero di caselle attive e ultimo controllo in Europe/Rome tramite un servizio applicativo indipendente dalle presentazioni; espone soltanto le tre azioni primarie `Controlla ora`, `Avvia` e `Pausa`, senza output tecnico o import legacy. Test task (`26 passed`), suite local connector e smoke (`399 passed`) verdi. Prossimo task `GUI-U-E2-T06 - Avvio, pausa e arresto`.

- 2026-07-16 - Completato `GUI-U-E2-T04`: il wizard gestisce una tabella di caselle persistenti con aggiunta, modifica e rimozione tramite un servizio applicativo condiviso; configurazioni Gmail/Workspace e IMAP personalizzate e relative credenziali restano indipendenti. Test task (`18 passed`), suite local connector e smoke (`391 passed`) verdi; nessun servizio reale usato. Prossimo task `GUI-U-E2-T05 - Home minima`.

- 2026-07-15 - Completato `GUI-U-E2-T03`: il wizard include la configurazione semplificata di una casella con quattro campi ordinari, default Gmail/Workspace, impostazioni avanzate richiudibili e verifica separata tramite servizio read-only iniettato, senza rete reale o termini vietati. Test task (`15 passed`), suite local connector e smoke (`387 passed`) verdi. Prossimo task `GUI-U-E2-T04 - Multi-account`.

- 2026-07-15 - Completato `GUI-U-E2-T02`: il primo avvio usa viste Benvenuto e Limbo distinte, sostituisce realmente i frame su avanti/indietro e applica validatori locali per passo senza accedere a rete o filesystem reale. Test task (`9 passed`), suite local connector e smoke (`381 passed`) verdi. Prossimo task `GUI-U-E2-T03 - Configurazione semplificata di una casella`.

- 2026-07-15 - Completato `GUI-U-E2-T01`: aggiunti il package indipendente `user_app`, la shell `Caronte`, il routing minimo tra primo avvio e Home tramite `ConfigurationService` e il comando `user-gui`, senza import o viste della GUI legacy. Test task (`5 passed`), suite local connector e smoke (`377 passed`) verdi. Prossimo task `GUI-U-E2-T02 - Wizard con schermate reali`.

- 2026-07-15 - Completato `GUI-U-E1-T04`: aggiunti l'adapter sostituibile per Windows Credential Manager, la factory del servizio credenziali e la traduzione tipizzata degli errori, senza nuove dipendenze o accessi reali. Test task (`9 passed`), suite local connector e smoke (`372 passed`) verdi; la sotto-epica E1 e` chiusa. Prossimo task `GUI-U-E2-T01 - Nuova shell user_app`.

- 2026-07-15 - Completato `GUI-U-E1-T03`: introdotti il contratto `CredentialStore`, il fake store in memoria e il servizio credenziali account sopra riferimenti strutturali, con CRUD tipizzato, isolamento multi-account e redazione dei valori da YAML, log, rappresentazioni ed errori. Test task (`7 passed`), suite local connector e smoke (`366 passed`) verdi. Prossimo task `GUI-U-E1-T04 - Backend credenziali Windows`.

- 2026-07-15 - Completato `GUI-U-E1-T02`: introdotti il modello strutturale e `ConfigurationService` indipendenti dai toolkit, con porta di persistenza, adapter YAML atomico, mappa campo-fonte e supporto multi-account; `scan-imap-accounts` riusa il servizio condiviso. Test task (`4 passed`), suite local connector e smoke (`363 passed`) verdi. Prossimo task `GUI-U-E1-T03 - Archivio credenziali astratto`.

- 2026-07-15 - Completato `GUI-U-E1-T01`: introdotto `ApplicationPaths` con configurazione in `%APPDATA%\Caronte` e dati in `%LOCALAPPDATA%\Caronte`, override assoluti e root iniettabili; tutti i consumer CLI dei dati locali usano il resolver condiviso senza dipendere da repository o cwd. Test mirati (`9 passed`), suite local connector e smoke (`359 passed`) verdi; il runbook dell'attivita` programmata fissa inoltre la venv corretta per `pytest`. Prossimo task `GUI-U-E1-T02 - Modello unico di configurazione`.

- 2026-07-15 - `GATE U-H1 = PASS` su decisione umana: approvati nomi, mappa dei servizi e percorso verticale minimo; l'implementazione `gui`/`gui_*` e` ora `ABANDONED_LEGACY`, mentre `Caronte Manutenzione` resta applicazione target con una nuova presentazione `maintenance_gui` separata. Architettura, mappa codice, backlog e documentazione operativa vietano il riuso della vecchia presentazione ma mantengono la suite di manutenzione tra i consumer dei servizi condivisi e i target di packaging. Prossimo task `GUI-U-E1-T01 - Percorsi applicativi Windows`; nessun codice applicativo modificato.

- 2026-07-15 - Completato `GUI-U-E0-T03`: classificati gli otto moduli GUI esistenti, assegnati servizi condivisi e destinazioni target, delimitate le lacune dei task E1-E3 e confermato che la GUI utente parte dalle attivita` senza trasformare comandi CLI in pulsanti. La scheda `GUI-U-E1-T01` rispetta la Definition of Done; `GATE U-H1` passa a `WAITING_HUMAN_REVIEW` e blocca E1 fino a esito umano esplicito. Nessun codice applicativo modificato.

- 2026-07-15 - Completato `GUI-U-E0-T02`: definita l'architettura target di `Caronte` separando `user_app`, `Caronte Manutenzione`, servizi applicativi condivisi, supervisore in background, dominio/porte, adapter locali, CLI e packaging. Fissati regole di import verificabili, contratti con consumer, responsabilita`, entry point definitive e percorso primo avvio -> due caselle -> Home -> avvio/pausa. Prossimo task `GUI-U-E0-T03 - Mappa del codice riutilizzabile`; nessun codice applicativo modificato.

- 2026-07-15 - Completato `GUI-U-E0-T01`: la GUI tecnica e` ora identificata come `Caronte Manutenzione`, avviabile con `maintenance-gui`; `gui` resta un alias deprecato con avviso esplicito. Titolo e avvertenza tecnica sono visibili senza aggiungere tab o funzioni; test mirati (`52 passed`), suite local connector e smoke (`353 passed`) verdi. Prossimo task `GUI-U-E0-T02 - Architettura della nuova applicazione`.

- 2026-07-15 - Completato `GUI-U-B01`: creato `docs/GUI_U_BACKLOG.md` con quattro sotto-epiche, task seriali, dipendenze, prove per criterio e tre gate umani; riscritta la Definition of Done con criteri misurabili e regole anti-loop; ridotti i puntatori operativi. Prossimo task `GUI-U-E0-T01 - Congelamento GUI tecnica`; nessun codice applicativo modificato.

- 2026-07-15 - Chiuso formalmente `V114-T17` come `CLOSED_AS_TECHNICAL_PROTOTYPE`: la GUI esistente resta un prototipo tecnico e strumento di assistenza, non una GUI utente finale, e sara` successivamente confinata come `Caronte Manutenzione`. Aperta l'iniziativa `GUI-U - Caronte Desktop utente`, fissati modulo, comandi ed eseguibili definitivi e impostato come prossimo task documentale `GUI-U-B01 - Backlog operativo e Definition of Done`; nessun codice applicativo modificato.

- 2026-07-14 - Completato V114-T17.9: aggiunti servizi e CLI condivisi `status-windows-task` e `uninstall-windows-task` per leggere stato, ultima esecuzione e ultimo esito e per rimuovere in modo confermato e idempotente il task Windows; il tab Automazione Win11 abilita piano, installazione, stato e rimozione con messaggi leggibili e senza scelta manuale di Python. Test mirati (`57 passed`), query locale read-only, suite local connector e smoke (`351 passed`) verdi; prossimo task V114-T17.10.

- 2026-07-14 - Completato V114-T17.8: rimosso il pannello globale `Parametri azioni`; Setup, Bucoliche, Avvio, Manutenzione e Automazione mostrano solo le rispettive impostazioni, mentre Python, formato export e cicli di prova restano nella Diagnostica avanzata. Cartella dati locali, scanner, intervallo e nome dell'avvio automatico sono validati e persistiti atomicamente nel file locale ignorato senza alterare le credenziali; Limbo e Bucoliche riusano il servizio del wizard. Test mirati (`29 passed`), suite local connector e smoke (`344 passed`) verdi; prossimo task V114-T17.9.

- 2026-07-14 - Completato V114-T17.7: il tab Monitoraggio proietta gli eventi locali in una tabella Europe/Rome con data/ora, casella, messaggio, allegato, azione, esito e problema; filtri combinabili coprono casella, esito, data ed errori, i problemi sono azionabili e la vista non espone JSON, path tecnici o segreti; test mirati (`21 passed`), suite local connector e smoke (`339 passed`) verdi; prossimo task V114-T17.8.

- 2026-07-14 - Completato V114-T17.6: la Home GUI mostra stato coerente col worker, caselle attive, controlli, completamenti, problemi e ultima/prossima verifica in Europe/Rome; scansione manuale, avvio continuo e stop sono le tre azioni primarie, senza output CLI grezzo; test sintetici, suite local connector e smoke verdi (`334 passed`); prossimo task V114-T17.7.

- 2026-07-14 - Completato V114-T17.5: la GUI esegue scansione singola e `watch` continuo tramite un processo gestito in background, con coda eventi, stati attivo/fermo/errore, rifiuto del doppio avvio e arresto deterministico anche alla chiusura; test fake coprono completamento, restart, stop, kill di fallback, errore e race in avvio; state, next tasks e backlog avanzati su V114-T17.6.

Registro avanzamento storico spostato fuori dal backlog attivo.

- 2026-07-14 - Completato `V114-T17.4`: la GUI account maschera le password per default e le mostra solo su scelta esplicita; credenziali aggiornabili e rimovibili persistono nel file locale ignorato con scrittura atomica, permessi restrittivi, nomi env deterministici e collisioni rifiutate; YAML e diagnostica GUI restano redatti; test mirati (`20 passed`), suite local connector e smoke (`326 passed`) verdi senza rete o credenziali reali; prossimo task `V114-T17.5`.
- 2026-07-14 - Completato `V114-T17.3`: il tab Account mail gestisce elenco, aggiunta, modifica, abilita/disabilita, rimozione e test IMAP read-only separato per casella tramite servizi applicativi condivisi; Gmail ha default noti e gli account generici mantengono server e cartelle distinti; test mirati (`21 passed`), suite local connector e smoke (`323 passed`) verdi senza rete o credenziali reali; prossimo task `V114-T17.4`.
- 2026-07-14 - Completato `V114-T17.2`: il tab Setup iniziale apre una procedura guidata riapribile Cartelle -> Caselle -> Registro condiviso -> Verifica finale, con navigazione avanti/indietro, due caselle sintetiche, validazioni azionabili, Bucoliche facoltativo e persistenza tramite il modello unico senza rete automatica o segreti nel YAML; test mirati (`17 passed`), suite local connector e smoke (`319 passed`) verdi; prossimo task `V114-T17.3`.
- 2026-07-14 - Completato `V114-T17.1`: aggiunto un servizio applicativo indipendente dalla GUI per load/validate/save atomico e CRUD del modello multi-account; YAML strutturale e valori locali restano coordinati, i segreti non entrano nel YAML, le sezioni non gestite vengono preservate e gli errori di scrittura ripristinano entrambi i file; test mirati (`54 passed`), suite local connector (`315 passed`) e smoke (`315 passed`) verdi; prossimo task `V114-T17.2`.
- 2026-07-14 - Riaperto `V114-T17` come `IN_PROGRESS - Collaudo UX non superato`: il collaudo manuale ha confermato che la GUI corrente e` un wrapper tecnico della CLI, non consente il percorso completo senza terminale e non e` utilizzabile come interfaccia finale. Definiti `V114-T17.1`...`V114-T17.10`, requisiti UX e fonti autorevoli della configurazione; prossimo task univoco `V114-T17.1`.
- 2026-07-08 23:55 +02:00 - Completato V114-T17: aggiunta al backlog la GUI completa Caronte locale come task finale v1.1.4; `virgilio gui` ora espone tab Stato, Setup iniziale, Account mail, Bucoliche, Avvio, Monitoraggio, Manutenzione, Automazione Win11 e Diagnostica avanzata, restando wrapper della CLI e disabilitando le azioni senza comando stabile; test mirati GUI, suite `pytest local_connector` (`310 passed`) e smoke locale (`310 passed`) verdi; aggiornata anche la programmazione `virgilio-sviluppo-autonomo`.
- 2026-07-08 22:31 +02:00 - Completato V114-T16: README, setup/test e workflow `clasp` ora spiegano in modo operativo installazione minima, primo avvio, test, uso quotidiano e troubleshooting; rimossi esempi con path personali per `install-windows-task`, corretto il riferimento stale a `apps_script\clasp` e confermati via help i comandi `pilot-preview`, `watch` e `install-windows-task`; state, next tasks e backlog chiudono la milestone v1.1.4 senza task operativi residui.
- 2026-07-08 15:36 +02:00 - Completato V114-T13 senza modifiche al codice: lo scaffold `init-config` e i loader `load_multi_account_config`/`load_storage_config` coprono la migrazione locale senza segreti in chiaro e con staging/folder configurabili; i test mirati su scaffold/init-config sono verdi, lo smoke locale e` verde (`303 passed`), e state/next tasks/backlog sono riallineati su V114-T14.
- 2026-07-08 21:05 +02:00 - Completato V114-T15: aggiunto `install-windows-task`, che registra il watch locale come task utente `ONLOGON` via Utilita` di Pianificazione con dry-run esplicito e senza servizi Windows; README e setup/test documentano il flusso; test mirati verdi (`5 passed`), suite `pytest local_connector` verde (`306 passed`) e smoke locale verde (`306 passed`) con `--basetemp` esterno per evitare il lock noto di `.pytest-tmp`.
- 2026-07-08 17:10 +02:00 - Completato V114-T14: aggiunto `watch`/`local-watch` come loop controllato della pipeline locale con `--interval-seconds` e `--max-cycles`; README, backlog, next tasks e state riallineati su V114-T15; suite `pytest local_connector` verde (`304 passed`) e smoke locale verde (`304 passed`).
- 2026-07-08 10:45 +02:00 - Completato V114-T12: aggiunto `reset-local-state` al local connector con backup sibling automatico, conferma esplicita e preservazione di `machine_id`; README e setup/test documentano il flusso, i test mirati e lo smoke locale sono verdi (`303 passed`), e state/next tasks/backlog sono riallineati su V114-T13.
- 2026-07-08 07:26 +02:00 - Completato V114-T11 senza toccare il codice: la GUI locale era gia` un wrapper controllato della CLI con test dedicati; `pytest local_connector` e smoke locale sono verdi, e state/next tasks/backlog sono riallineati su V114-T12.
- 2026-07-07 23:25 +02:00 - Completato V114-T10: `init-config` e `LocalStorageConfig` rifiutano `storage.staging_dir` relativi, README e setup/test chiariscono il path assoluto richiesto, i test mirati passano e lo smoke locale e` verde; state, next tasks e backlog riallineati su V114-T11.
- 2026-07-07 18:03 +02:00 - Completato V114-T02-bis: esempi e codice di configurazione non espongono piu` il doppione single-account negli esempi principali, `stage-ready-files` usa `VIRGILIO_LIMBO_LOCAL_SYNC_DIR` e l`account_alias` per-riga, e il legacy Apps Script Bucoliche converge sul tab `Bucoliche_Eventi`; backlog/state/next tasks riallineati su V114-T10.
- 2026-07-07 08:38 +02:00 - Completato V114-T08: tutti i timestamp operativi del local connector e il seed Apps Script inbox sono stati riallineati su `Europe/Rome`, il Registro locale ora espone `timestamp` invece di `timestamp_utc`, i test mirati e lo smoke locale sono verdi, e state/next tasks/backlog sono riallineati su V114-T09.
- 2026-07-07 13:25 +02:00 - Completato V114-T09: `docs/CLASP_WORKFLOW.md` ora esplicita la sequenza manuale Caronte (credenziali -> verifica configurazione -> trigger -> stato -> stop -> test minimo) distinta dal flusso di produzione; state, next tasks e backlog riallineati su V114-T10.
- 2026-07-06 22:35 +02:00 - Completato V114-T06: `apps_script/src/setup.gs` ora accetta credenziali a runtime o via Script Properties senza placeholder nel sorgente; i hint di stato puntano alla configurazione esplicita; parse in-memory di `setup.gs` e `py_compile` di `local_connector/src/virgilio_connector/__main__.py` verdi; state, next tasks e backlog riallineati su V114-T07.
- 2026-07-07 07:55 +02:00 - Completato V114-T07: `local_connector/src/virgilio_connector/policy.py` estende l'allowlist ai formati Office con scansione obbligatoria; i test locali di policy/quarantena/orchestrator, `pytest local_connector` e `scripts/dev/smoke_local_connector.ps1` sono verdi; `apps_script/src/caronte_bridge.gs` e `apps_script/src/virgilio_inbox.gs` ora usano un `policy_rule` neutro `scan_obbligatoria`; state, next tasks e backlog riallineati su V114-T08.
- 2026-07-06 17:28 +02:00 - Completato V114-T05: hardening segreti locale confermata su `local_connector` senza esporre valori sensibili; test mirati su `doctor`/multi-account e smoke `scripts/dev/smoke_local_connector.ps1` verdi; state, next tasks e backlog riallineati su V114-T06.
- 2026-07-06 12:25 +02:00 - Completato V114-T04: `local_connector/.env.example` usa ora alias neutri e due account generici, `docs/ARCHITETTURA_UNIFICATA.md` lo esplicita, lo smoke locale e` verde e backlog/state/next tasks sono riallineati su V114-T05.
- 2026-07-06 11:45 +02:00 - Completato V114-T02: il flusso unico ora esplicita Quarantena locale eventuale e Limbo Drive unico in README/architettura; backlog, state e next tasks riallineati su V114-T03.
- 2026-07-06 11:38 +02:00 - Completato V114-T01: il profilo dopo il collaudo resta esplicito in README e architettura; backlog attivo, state e next tasks avanzati su V114-T02.
- 2026-07-06 12:15 +02:00 - Completato V114-T03: README e architettura erano gia` allineati su Google-only mono-account e Local connector multi-casella/IMAP; state, next tasks e backlog riallineati su V114-T04.
- 2026-07-05 18:46 +02:00 - GAS riportato davvero alla v1.1.3: il live pull ha mostrato il mirror remoto ancora vecchio, il mirror e` stato ricostruito da `apps_script/src`, `clasp push -f` e deploy `@28` sono stati completati e lo stato operativo e` stato aggiornato.
- 2026-07-04 12:19 +02:00 - Aggiornati `docs/GAS_PUSH_REPORT_20260704.md`, `docs/GAS_V113_EVIDENCE_MATRIX_20260704.md` e `docs/CODEX_STATE.md` dopo il push completato: il mirror `apps_script/clasp` e` stato riallineato da `apps_script/src`, la pubblicazione e` andata a buon fine e la readiness GAS e` ora `GO`.
- 2026-07-04 12:00 +02:00 - Aggiunti `docs/GAS_V113_EVIDENCE_MATRIX_20260704.md` e `docs/GAS_PUSH_REPORT_20260704.md`: la base canonica e` `apps_script/src`, il mirror precedente e` stato archiviato in `apps_script/archive/pre_push_gas_20260704_114328/`, la sync locale e lo smoke sono verdi, ma `clasp pull`/`clasp push` falliscono con `invalid_grant / invalid_rapt` senza toccare `.clasprc.json`.
- 2026-07-04 11:21 +02:00 - Aggiunto `docs/GAS_READINESS_20260704.md` con esito `NO_GO`: il mirror Apps Script non e` allineato alla sorgente canonica, il bridge inbox/form/notifiche piu` nuovo e` presente solo in `src` e `clasp push` resta fermo finche` non si sincronizza il layout.
- 2026-07-04 10:57 +02:00 - Rifatti report e readiness sui collaudi reali del local connector: 291 test e smoke verdi, `doctor`/`pilot-run`/`doctor-bucoliche`/`pilot-preview` verificati, due `pilot-run` reali consecutivi idempotenti; corretto anche `doctor-bucoliche` CLI con summary dedicato e regression test.
- 2026-07-04 10:24 +02:00 - Aggiornata la documentazione di setup/readiness con i binari locali reali `node/npm/clasp`, la verifica `clasp status` eseguita via entrypoint esplicito e le istruzioni per i collaudi locali del connector senza toccare GAS.
- 2026-07-04 10:06 +02:00 - Aggiunto `docs/TEST_READINESS_20260704.md` e riallineati `README.md` e `docs/SETUP_AND_TEST.md` sul runtime verificato `local_connector\.venv\Scripts\python.exe`, sullo smoke offline raccomandato e sul blocco noto dell'install editable offline senza `setuptools`; preparati anche i comandi sicuri per env IMAP e verifica `clasp`.
- 2026-07-04 09:36 +02:00 - Aggiunto `docs/TEST_REPORT_20260704.md` con esito `PASS_WITH_WARNINGS`: `pytest local_connector` e smoke offline verdi, `doctor`/`pilot-run --dry-run` bloccati da env IMAP mancanti, `pip install -e .\local_connector` non autosufficiente offline e `clasp` non disponibile nell'ambiente corrente.
- 2026-07-04 02:35 +02:00 - Completato V113-E6-T04: il README normalizza la UX iniziale senza esporre dettagli macchina; backlog, state e next tasks riallineati.
- 2026-07-04 01:35 +02:00 - Completato V113-E6-T03: README e setup/test separano test controllati e collaudi reali; backlog, state e next tasks riallineati.
- 2026-07-03 23:37 +02:00 - Completato V113-E6-T01: README, architettura e workflow clasp distinguono i profili Google-only e Local connector; backlog e state riallineati.
- 2026-07-03 19:34 +02:00 - Completato V113-E4-T04: `intake-da-archiviare` scrive ora un audit locale in `audit_events` e `export-registro-events` lo proietta come fase `da archiviare`; test mirati, suite `pytest local_connector` e smoke locale verdi.
- 2026-06-29 - Report pipeline arricchito con `human_summary` leggibile e sicura; test report verdi.
- 2026-06-29 - `pilot-run-safe` aggiunto come wrapper dry-run con stop su gate; test CLI/sequenza verdi.
- 2026-06-29 - `Bucoliche_Stato` rigenerato dagli eventi durante export; test fake/idempotenza verdi.
- 2026-06-30 - Aggiunto `refresh-bucoliche-state`: rigenera solo `Bucoliche_Stato` da eventi locali, con dry-run che mostra preview e senza append su `Bucoliche_Eventi`.
- 2026-06-30 - Doppio run end-to-end reso idempotente: export Bucoliche ignora eventi senza fingerprint e la completion registra eventi per allegato solo al primo completamento utile.
- 2026-06-30 - Manifest e SQLite usano l'email operativa risolta da `username_env` quando disponibile, evitando l'export di `example.invalid` dai config placeholder.
- 2026-06-30 - Export centrale e Bucoliche ora saltano i record legacy con `attachment_id=None` rilevati come `legacy_incomplete`, senza toccare gli eventi sintetici validi.
- 2026-06-30 - Aggiunto test di regressione sul secondo export Bucoliche gia marcato `exported`: nessun nuovo append su `Bucoliche_Eventi`, `Bucoliche_Stato` continua a rigenerarsi.
- 2026-06-30 - Aggiunto il comando unico `virgilio pilot`: wrapper dry-run con preview integrato, exit code coerente ed entrypoint console dedicato.
- 2026-06-30 - `run-local-pipeline`, `pilot-preview`, `pilot-run-safe` e `virgilio pilot` supportano `--human` per uno snapshot leggibile, mantenendo il JSON come output predefinito per script e automazioni.
- 2026-06-30 - Aggiunto `virgilio init-config`: genera uno scheletro `accounts.local.yaml` valido e senza segreti nel file, con sezioni account/storage/Bucoliche/rules e note sulle env locali.
- 2026-06-30 - `doctor` ora espone suggerimenti azionabili sugli errori ricorrenti e supporta `--human` per una diagnosi locale leggibile senza segreti.
- 2026-06-30 - Coperti nei test due `machine_id` isolati: `load_machine_id` resta stabile per root locale e l'export Bucoliche preview conserva due eventi distinti sullo stesso fingerprint.
- 2026-06-30 - L'export Bucoliche ora ordina gli eventi in modo deterministico per timestamp, fingerprint e macchina, cosi due export equivalenti da postazioni diverse producono lo stesso merge anche con `audit_events.id` invertiti.
- 2026-06-30 - `Bucoliche_Stato` ora consolida davvero il cross-machine: una sola riga per fingerprint, `machine_id` aggregati in modo deterministico e note marcate `cross_machine` quando lo stesso allegato arriva da piu postazioni.
- 2026-06-30 - `Bucoliche_Stato` segnala `conflict_cross_machine` quando lo stesso fingerprint arriva da piu macchine con esiti terminali incompatibili, includendo `machine_states` nelle note senza risoluzione automatica.
- 2026-06-30 - Aggiunto `litellm-gateway-dry-run`: adapter LiteLLM futuro mock-only con budget locale su token/costo, senza rete ne dipendenze LiteLLM, pronto per la futura classificazione assistita.
- 2026-06-30 - Documentata la policy manuale per `conflict_cross_machine`: triage su `state.db`, macchina autorevole unica, nessuna modifica manuale ai tab Bucoliche e nessuna risoluzione automatica.
- 2026-06-30 - `local_connector/README.md` ora include la sezione "10 comandi essenziali" con il flusso locale minimo v1.1 allineato alla CLI corrente.
- 2026-06-30 - Aggiunto `compare-parser-fixtures`, spike isolato che confronta snapshot Docling/Unstructured su fixture sintetiche e produce un report locale di qualita senza dipendenze o parsing reale.
- 2026-06-30 - Aggiunto `extract-local-fixtures`: parser locale `stdlib_local` che estrae testo e tabelle minime da fixture sintetiche `PDF/DOCX/XLSX` con sole librerie standard, fuori dalla pipeline produttiva.
- 2026-06-30 - Il manifest locale e staged ora include anche metadati retrocompatibili di provenienza e decisione (`source_sender`, `source_mailbox`, `source_message_date`, `source_thread_id`, `file_extension`, `policy_*`, `status_reason`) senza cambiare i consumer esistenti.
- 2026-06-30 - Aggiunto `classify-manifest-dry-run`: legge un manifest locale, propone una classificazione prudente con review obbligatoria e allega il responso mock LiteLLM senza reti o azioni automatiche.
- 2026-06-30 - Aggiunto `review-classification-dry-run`: accetta solo proposte locali `dry_run` con `review_required=true`, registra approvazione/rifiuto umano e mantiene il workflow futuro senza azioni automatiche.
- 2026-06-30 - Aggiunto `classification-feedback-dry-run`: accetta solo review locali `dry_run` completate, traccia la classificazione finale e distingue tra conferma e correzione manuale senza scrivere stato operativo.
- 2026-06-30 - Aggiunto `ack-completed-messages`: wrapper esplicito per il completion reale con dry-run separato e gate locali su export Bucoliche gia registrato, conflitti candidate-specific e stato ackabile prima di aprire IMAP in scrittura.
- 2026-07-01 - Hardened l'ack IMAP prudente `add_done_label_only`: verifica `done_folder` via `IMAP LIST` prima del `UID COPY`, usa quoting sicuro dei mailbox name e restituisce diagnostica esplicita su `done_folder`, stato IMAP e suggerimento "Mostra in IMAP" senza introdurre move/delete/store.
- 2026-07-01 - Aggiunto `pilot-run`: comando unico v1.1 che orchestra `doctor`, pipeline, conflitti, export Bucoliche e ack prudente con report locale `pilot_run_v11_*.json`, mantenendo `virgilio pilot` come preview compatibile.
- 2026-06-30 - Aggiunto `virgilio gui`: GUI minima locale in `tkinter` che fa da wrapper a `init-config`, `doctor` e `pilot`, costruendo argomenti CLI e mostrando l'output senza duplicare la logica operativa.
- 2026-07-01 - Definito il mapping stabile `manifest locale -> Virgilio_Inbox`: `caronte_bridge.gs` espone il draft puro della riga inbox, `drive_staging_verify.gs` restituisce `inbox_preview` read-only con i campi gia valorizzabili dal manifest e lascia vuoti i campi demandati ai task successivi (`inbox_id`, suggerimenti, `form_url`).
- 2026-07-01 - Aggiunto `virgilio_inbox.gs`: setup esplicito e consolidamento non distruttivo dello schema `Virgilio_Inbox`, con header canonico a 22 colonne, `inbox_id` in prima posizione e rifiuto dei mismatch su tab gia popolati.
- 2026-07-01 - Completato `V112-E1-T03`: `caronteRegistraVirgilioInbox` esegue l'intake metadata-only sul tab `Virgilio_Inbox`, genera `inbox_id`, usa `fingerprint` come chiave primaria con fallback `attachment_id`, evita duplicati sul retry e rifiuta conflitti `sha256` o payload con path locali / base64.
- 2026-07-01 - Completato `V112-E1-T04`: l'intake `Virgilio_Inbox` ora richiede `drive_file_id` e `manifest_file_id` restituiti dalla verify read-only, ricontrolla che file e manifest siano davvero visibili nella cartella Drive configurata e blocca mismatch o intake senza conferma cloud.
- 2026-07-01 - Completato `V112-E2-T01`: `doGet(e)` legge `inbox_id`, `webapp.gs` passa al template solo contesto read-only da `Virgilio_Inbox`, `virgilio.html` mostra il riepilogo documento e precompila in modo non invasivo eventuali suggerimenti gia presenti senza toccare il submit operativo.
- 2026-07-01 - Completato `V112-E2-T02`: `virgilio.html` passa `inbox_id` al submit, `caronte.gs` rifiuta i submit con `inbox_id` non correlato e `virgilio_inbox.gs` aggiorna il record esistente con stato `in_lavorazione` e contesto umano minimo del form senza creare un inbox nuovo.
- 2026-07-01 - Completato `V112-E2-T03`: `doPost` usa ora l `inbox_id` per archiviare l allegato Drive puntuale del record `Virgilio_Inbox` dentro `02_corrispondenza`, mantiene il fallback temporale legacy solo senza inbox e marca il record inbox come `archiviato` con traccia della destinazione finale.
- 2026-07-01 - Completato `V112-E2-T04`: il ramo `doPost` con `inbox_id` registra ora su `bucoliche` un esito finale coerente (`stato=archiviato`, nome file, note correlate all inbox) e invia notifiche dedicate Chat/Telegram che confermano pratica aperta e documento archiviato, senza cambiare il flusso legacy senza inbox.
- 2026-07-01 - Completato `V112-E3-T01`: il README ora separa comandi base e collaudo controllato, con `--dry-run` esplicitato come test e il run reale riservato a configurazioni gia' verificate.
- 2026-07-01 - Completato `V112-E3-T02`: `setup.gs` ora mostra un riepilogo operativo unico di credenziali, URL form ed endpoint trigger con hint espliciti, senza stampare valori sensibili.
- 2026-07-01 - Completato `V112-E3-T03`: la roadmap v1.1.2 ora riassume il flusso utente finale con i passi `Virgilio_Inbox -> form -> submit -> archiviazione -> Bucoliche -> notifiche`, senza introdurre nuova logica applicativa.
- 2026-07-03 - Task 0.0 chiuso: la sorgente canonica vive in `apps_script/src` e la snapshot `clasp` in `apps_script/clasp`, con root libera da file Apps Script ambigui.
- 2026-07-03 - `docs/ARCHITETTURA_UNIFICATA.md` e` il riferimento condiviso per lessico e flusso, con link in `README.md` e `AGENTS.md`.
- 2026-07-03 - Mappati i termini legacy nel lessico ufficiale: tabella di equivalenza in `docs/ARCHITETTURA_UNIFICATA.md` e backlog allineato al vocabolario unico.
- 2026-07-03 - Completato `V113-E1-T01`: definito lo schema minimo del Registro in `docs/ARCHITETTURA_UNIFICATA.md`, con backlog e next tasks riallineati.
- 2026-07-03 - Completato `V113-E1-T02`: il local connector espone la proiezione Registro `export-registro-events` / `registro_event_rows()` e il backlog e` riallineato sul prossimo task di errori e conflitti.
- 2026-07-03 - Completato `V113-E0-T01`: mappa minima delle funzioni da preservare in `docs/ARCHITETTURA_UNIFICATA.md`, con backlog e next tasks riallineati.
- 2026-07-03 - Completata la classificazione dei moduli Google-only e local connector: `README.md` e `docs/ARCHITETTURA_UNIFICATA.md` distinguono sorgente Apps Script canonica, snapshot `clasp` e local connector; backlog aggiornato a DONE.
- 2026-07-03 - Completato `V113-E1-T03`: `registraErrore()` e `registraConflitto()` traducono gli errori Google-only in eventi di audit leggibili, con conflitti inbox registrati prima del throw; backlog e next tasks riallineati.
- 2026-07-03 - Completato `V113-E2-T01`: schema minimo di `Da archiviare` definito in `docs/ARCHITETTURA_UNIFICATA.md`, con coda a singola riga per documento, campi core e stati `da_lavorare` / `in_lavorazione` / `archiviato`; backlog e next tasks riallineati.
- 2026-07-03 - Consolidata `Virgilio_Inbox` come coda tecnica nella roadmap v1.1.2; backlog riallineato sul primo TODO P0 non bloccato successivo.
- 2026-07-03 09:50 Europe/Rome - Completato il task `Esporre Da archiviare nella UX`: `README.md` e `docs/VIRGILIO_V112_INTEGRATION_ROADMAP.md` ora espongono `Da archiviare` nella UX con `Virgilio_Inbox` come tab tecnico; backlog riallineato a DONE; runtime circa 20 minuti.
- 2026-07-03 14:48 Europe/Rome - Completato `V113-E3-T01`: `caronteTraghetta()` registra ora `Virgilio_Inbox` per gli allegati Gmail salvati nel Limbo, con adapter Gmail-only metadata-only e test puri + smoke locali verdi; backlog e next tasks riallineati.
- 2026-07-03 16:33 +02:00 - Completato `V113-E4-T01`: aggiunto `build_da_archiviare_intake_payload()` nel local connector per comporre il payload metadata-only verso `Da archiviare` senza `test_mode` e senza campi vietati; backlog, next tasks e reference architetturale riallineati.
- 2026-07-03 - Completato `V113-E4-T03`: il local connector crea o aggiorna il record `Da archiviare` con `intake-da-archiviare`, `DaArchiviareIntakeHttpClient.create_record()` e dispatch `doPost` dedicato; test mirati, suite `pytest local_connector` e smoke locali verdi.
- 2026-07-03 20:35 Europe/Rome - Completato `V113-E5-T02`: il submit mantiene il legame con il record `Virgilio_Inbox` corretto; backlog e next tasks riallineati sul passo successivo `V113-E5-T03`.
- 2026-07-03 23:15 +02:00 - Completato `V113-E5-T03`: `doPost` espone ora `inbox_status=archiviato`, la notifica archiviazione include lo stato finale e la schermata di successo mostra l'esito inbox; backlog, next tasks e state riallineati su `V113-E6-T01`; test mirati Apps Script e parsing HTML locale verdi.
# 2026-07-28

- Completato `CONS-H01`: onboarding unico da clone pulito con bootstrap del
  venv dalla dichiarazione `pyproject.toml`; prova isolata senza credenziali,
  help CLI e smoke completo `548 passed`.

- Completato `CONS-R02`: README e changelog ufficiale descrivono la release
  `1.1.0`, il percorso desktop collaudato, prerequisiti e limiti correnti;
  gli artefatti `0.11.0-<commit>` restano distinti come RC storiche. Controlli
  documentali e smoke locale `600 passed`.

# 2026-07-25

- Completato `GUI-U-R04-R04`: il controllo Home riceve avanzamenti strutturati
  dalla pipeline senza duplicarla, mostra fase e soli conteggi noti, mantiene un
  unico runner per controllo/pause e redige attese/errori in messaggi azionabili.
  Test mirati `113 passed`, Tk reale `1 passed`, smoke locale `549 passed`.

- Consolidato il `FAIL` umano della RC `bab6e92`: il percorso locale crea la
  coda tecnica ma non notifica ne` rende raggiungibile il lavoro in Virgilio;
  registrate inoltre lentezza senza avanzamento osservabile e semantica
  fuorviante di `Cartella completati`. Pianificati quattro task autonomi
  `GUI-U-R04-R03`--`R04-R06` e due gate umani finali (pubblicazione Apps Script
  e pilota reale).
- 2026-07-28 - Completato `CONS-C04`: selezionato con metriche `multi_account.py` come primo modulo operativo monolitico non GUI ed estratto il parser YAML locale in `local_config_yaml.py`. Dipendenza unidirezionale, API ed errori pubblici invariati; test mirati `80 passed`, smoke locale `546 passed`. Successore `CONS-C05`.
