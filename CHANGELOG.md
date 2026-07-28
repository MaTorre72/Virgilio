# Changelog

## 1.1.0 - 2026-07-28

Prima release ufficiale del percorso desktop consolidato di Virgilio.

### Funzioni

- Applicazioni separate **Caronte** e **Caronte Manutenzione**, basate sugli
  stessi servizi applicativi e senza dipendenze dalla GUI legacy.
- Flusso verificabile email -> quarantena locale -> Limbo Drive ->
  **Da archiviare** -> form -> pratica finale -> Registro.
- Acquisizione IMAP multi-casella, controllo manuale o continuo, riprese
  idempotenti, quarantena, scansione e policy sugli allegati.
- Coda tecnica unica `Virgilio_Inbox` e Registro cloud umano unico `bucoliche`,
  con stato e conflitti tecnici conservati localmente.
- Notifiche, archiviazione guidata e completamento della mail soltanto dopo
  l'archiviazione di tutti i documenti correlati.
- Setup, diagnostica, backup e reset coordinato nella superficie di
  manutenzione; credenziali conservate nel deposito protetto locale.

### Correzioni consolidate

- Verifica e retry limitati durante la latenza di sincronizzazione del Limbo,
  senza ripetere intake gia` riusciti.
- Registro append-only condiviso tra Apps Script, CLI e GUI, senza tab cloud
  paralleli.
- Completamento Gmail verificato dopo copia dell'etichetta finale e rimozione
  della sola etichetta di ingresso, senza `DELETE`, `MOVE` o `EXPUNGE`.
- Follow-up persistente tra consegna, archiviazione e completamento, senza nuove
  acquisizioni o falsi completamenti.
- Parsing ricorsivo degli allegati MIME annidati, identita` IMAP stabile tra
  cicli e avviso esplicito per mail senza allegati utilizzabili.
- Reset con lock, backup verificati e conservazione di configurazione,
  credenziali, identita` macchina e anagrafiche canoniche.

### Prerequisiti e limiti

- Windows 11, Google Drive per desktop, casella IMAP e deployment Apps Script
  configurati come descritto nel README.
- La sincronizzazione Drive puo` richiedere retry; macro, archivi compressi ed
  eseguibili restano bloccati; i formati Office ammessi richiedono scansione.
- AI, RAG, Docling, LiteLLM, database remoti e server web non fanno parte della
  release.
- Le operazioni reali, i reset e i deploy richiedono autorizzazione dedicata.

### Release candidate storiche

Gli artefatti `0.11.0-<commit>` erano RC identificabili usate durante il
collaudo. La RC baseline `0.11.0-7e18277` ha ricevuto `PASS` umano il 2026-07-28;
resta un'evidenza storica e non e` la release ufficiale `1.1.0`.

## 1.0

- MVP Google Workspace mono-utente.
- Interfaccia Virgilio HTML, Caronte, Drive e Limbo.
- Bucoliche come registro operativo su Google Sheets.
- Notifiche Google Chat e Telegram.
