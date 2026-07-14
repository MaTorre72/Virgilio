# Backlog di sviluppo

Nota: lo storico, i completamenti chiusi e le milestone finite sono stati spostati in
`docs/DEV_BACKLOG_ARCHIVE.md`; il registro datato e` in `docs/CHANGELOG_DEV.md`.
Le fonti operative leggere restano `docs/CODEX_STATE.md` e `docs/NEXT_CODEX_TASKS.md`.

Stati: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`. Qui restano solo task attivi o bloccati.

## Milestone v1.1.4 - Rifinitura collaudo, setup e hardening

Obiettivo: consolidare collaudo, setup e hardening prima di qualunque rifinitura di UX,
mantenendo task piccoli, seriali, verificabili e doc-first.

Nota operativa: il collaudo UX manuale del 2026-07-14 non e` stato superato.
`V114-T17` e` riaperto e il prossimo task univoco e` `V114-T17.10`.

| ID | Stato | Pri | Obiettivo | Ambito | Criteri di accettazione | Vincoli |
|---|---|---|---|---|---|---|
| V114-T02 | DONE | P0 | Flusso unico e cartelle | `docs/ARCHITETTURA_UNIFICATA.md`, `README.md` | il flusso `Acquisizione -> Quarantena locale eventuale -> Limbo Drive unico -> Da archiviare -> Form -> Pratica finale -> Registro` e` univoco e non ambiguo | non introdurre un secondo Limbo; non confondere Quarantena locale con la cartella condivisa |
| V114-T02-bis | DONE | P0 | Pulizia configurazione extra post-allineamento | `local_connector/.env.example`, `local_connector/accounts.example.yaml`, `local_connector/src/virgilio_connector/`, `apps_script/src/` | gli esempi principali sono solo multi-account, il sync locale del Limbo e` distinto ma non alternativo al Limbo Drive, e Bucoliche non dipende piu` dal tab generico `bucoliche` | task extra fuori sequenza v1.1.4; non cambia il prossimo task regolare |
| V114-T03 | DONE | P0 | Modi operativi supportati | `docs/ARCHITETTURA_UNIFICATA.md`, `README.md` | Google-only risulta mono-account; Local connector risulta multi-casella; una casella Google Workspace puo` essere letta via IMAP dal Local connector | non mischiare i profili; non aprire un flusso parallelo; non usare servizi reali |
| V114-T04 | DONE | P1 | Configurazione multi-account neutra | `local_connector/.env.example`, `docs/ARCHITETTURA_UNIFICATA.md` | esempi e alias sono neutri, almeno due account generici sono previsti e non compaiono riferimenti personali | niente dati personali; niente indirizzi reali; niente alias instabili |
| V114-T05 | DONE | P1 | Secrets hardening locale | `local_connector/`, `README.md`, `docs/SETUP_AND_TEST.md` | `.env`, password, token e log sono trattati in modo sicuro; la configurazione viene validata senza esporre segreti | segreti mai nel sorgente; log mascherati; no servizi reali |
| V114-T06 | DONE | P1 | Secrets e setup GAS | `apps_script/src/`, `docs/CLASP_WORKFLOW.md`, `README.md` | nessuna procedura chiede di scrivere segreti nei `.gs`; il setup usa Script Properties e verifica configurazione | non mettere segreti nel codice; non cambiare il form; non usare `clasp push` fuori dal task |
| V114-T07 | DONE | P1 | Office attachments policy | `docs/ARCHITETTURA_UNIFICATA.md`, `apps_script/src/`, `local_connector/` | `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx` sono ammessi solo con scansione obbligatoria; macro-enabled, archivi compressi ed eseguibili restano bloccati | non indebolire i gate di scan; non introdurre nuove categorie di file |
| V114-T08 | DONE | P1 | Timestamp Europe/Rome only | `apps_script/src/`, `local_connector/`, `docs/ARCHITETTURA_UNIFICATA.md` | tutti i timestamp operativi usano `Europe/Rome`; non compaiono campi UTC, nemmeno interni, in SQLite, manifest, log o Google Sheet | no UTC; no conversioni ambigue; no campi tecnici duplicati |
| V114-T09 | DONE | P1 | GAS setup e trigger Caronte | `apps_script/src/`, `docs/CLASP_WORKFLOW.md` | la sequenza setup properties -> verifica configurazione -> setup trigger -> stato trigger -> stop trigger -> test minimo e` lineare e distinguibile da produzione | non confondere test e produzione; non saltare la verifica configurazione |
| V114-T10 | DONE | P1 | Setup CLI ready-to-run | `local_connector/`, `README.md`, `docs/SETUP_AND_TEST.md` | i comandi CLI di setup, validazione percorsi, cartelle locali, Limbo e Sheet sono chiari e pronti all'uso per un utente non tecnico | la GUI non precede la CLI; no servizi reali; no nuovi tool inutili |
| V114-T11 | DONE | P2 | GUI installazione locale fase 1 | `local_connector/`, `README.md` | la GUI resta solo un wrapper controllato della CLI per configurazione iniziale, test, stato e messaggi | non creare una nuova applicazione parallela; non riscrivere la CLI |
| V114-T12 | DONE | P3 | Reset locale sicuro | `local_connector/`, `README.md`, `docs/SETUP_AND_TEST.md` | esiste `reset-local-state --backup --confirm`, con backup automatico, conferma esplicita e messaggi chiari | priorita` bassa; backup obbligatorio; nessuna cancellazione implicita |
| V114-T13 | DONE | P3 | Migrazione installazione locale | `local_connector/`, `README.md`, `docs/SETUP_AND_TEST.md` | export/import configurazione funzionano senza segreti in chiaro e supportano cambio PC o cartelle | priorita` bassa; nessun segreto in chiaro; nessun dato personale |
| V114-T14 | DONE | P2 | Avvio Caronte locale | `local_connector/`, CLI utente finale, `README.md` | esiste `virgilio watch` o `virgilio local-watch` che avvia il connettore e resta in attesa controllando la mail con polling controllato | un solo comando utente finale; niente GUI nuova; niente polling fuori controllo |
| V114-T15 | DONE | P3 | Installazione automatica Win11 | `local_connector/`, `README.md`, `docs/SETUP_AND_TEST.md` | esiste un comando per l'esecuzione automatica su Windows 11 tramite Utilita di Pianificazione | solo Windows 11; niente servizi residenti; niente installazioni silenziose ambigue |
| V114-T16 | DONE | P2 | Documentazione utente finale | `README.md`, `docs/SETUP_AND_TEST.md`, `docs/CLASP_WORKFLOW.md` | installazione minima, primo avvio, test, uso quotidiano e troubleshooting sono spiegati in modo operativo | niente segreti, niente termini macchina superflui, niente nuove procedure non testate |
| V114-T17 | IN_PROGRESS | P1 | GUI completa Caronte locale - Collaudo UX non superato | `local_connector/`, documentazione GUI | un utente medio completa setup, gestione di almeno due caselle, prova, avvio, arresto, attivita`, automazione Windows e manutenzione senza terminale o editing manuale di YAML/`.env` | task ombrello; chiudere solo dopo `V114-T17.1`...`V114-T17.10`; condividere servizi con la CLI; no GUI web o logica duplicata |
| V114-T17.1 | DONE | P0 | Modello unico configurazione GUI | servizi configurazione, YAML, valori locali, test | API applicative indipendenti dalla GUI leggono, validano e scrivono il modello unico; una sola fonte autorevole per dato; aggiornamenti coerenti e recuperabili | primo task; niente segreti nel YAML/log; nessuna modifica manuale richiesta all'utente |
| V114-T17.2 | DONE | P0 | Wizard primo avvio | GUI setup, servizi di T17.1 | procedura Cartelle -> Caselle -> Registro condiviso -> Verifica finale, riapribile e guidata | dipende da T17.1; niente termini tecnici nella vista ordinaria |
| V114-T17.3 | DONE | P0 | Gestione multi-account completa | servizi account e GUI | elenco, aggiunta, modifica, abilita/disabilita, rimozione e test read-only separato per almeno due caselle | dipende da T17.2; account e server distinti; niente servizi reali nei test |
| V114-T17.4 | DONE | P0 | Gestione sicura credenziali | archivio locale e GUI account | password mascherate, mostra/nascondi, persistenza locale, nomi stabili e redazione log | dipende da T17.3; nessun segreto versionato o nel sorgente |
| V114-T17.5 | DONE | P0 | Avvio e arresto non bloccanti | runner/worker e GUI | controllo singolo, continuo e stop funzionano senza blocchi, doppi avvii o processi orfani | dipende da T17.4; riusare servizi applicativi; niente `subprocess.run` continuo nel thread GUI |
| V114-T17.6 | DONE | P1 | Home operativa | stato e metriche GUI | stato, contatori, ultima/prossima verifica e tre azioni primarie sono leggibili | dipende da T17.5; niente output CLI grezzo |
| V114-T17.7 | DONE | P1 | Vista Attivita` leggibile | eventi locali e GUI | tabella Europe/Rome filtrabile per casella, esito, data ed errore, con messaggi comprensibili | dipende da T17.6; niente JSON ordinario o segreti |
| V114-T17.8 | DONE | P1 | Impostazioni contestuali | GUI impostazioni | rimosso il pannello globale `Parametri azioni`; ogni campo appare solo nel proprio contesto | dipende da T17.7; dettagli tecnici solo in diagnostica avanzata |
| V114-T17.9 | DONE | P1 | Automazione Windows completa | servizi Task Scheduler e GUI | installazione, stato, ultimo esito e rimozione sono gestibili senza terminale | dipende da T17.8; Windows 11, CLI-first condivisa, niente servizi residenti |
| V114-T17.10 | TODO | P0 | Collaudo utente finale | intero percorso GUI | da zero: due caselle, persistenza, prova sicura, avvio/stop, attivita`, automazione e manutenzione senza terminale | dipende da T17.9; collaudo manuale obbligatorio; nessun account o dato reale nei test automatici |

### Esito collaudo UX V114-T17

Il precedente criterio di completamento verificava la copertura dei comandi CLI,
non l'usabilita` del percorso finale. Il collaudo manuale ha rilevato un solo set
di campi account, assenza di password e persistenza coordinata, esposizione di
YAML/Python/termini tecnici, parametri globali non contestuali, azioni centrali
disabilitate e monitoraggio sincrono senza arresto. La GUI corrente e` pertanto un
prototipo tecnico e non deve essere descritta come completa. Requisiti e fonti
autorevoli sono in `docs/GUI_UX_REQUIREMENTS.md`.

### V114-T17.1 - Modello unico configurazione GUI

- **Obiettivo:** creare servizi indipendenti dalla GUI per un modello unico che coordini YAML e file locale.
- **Dipendenze:** nessuna; e` il fondamento obbligatorio di tutta la sequenza.
- **Ambito:** load/validate/save atomico, migrazione doppioni, alias e nomi env stabili, API CRUD testabili.
- **Criteri di accettazione:** round-trip multi-account senza perdite; `account_alias` solo nel YAML; `storage.staging_dir` unica fonte Limbo; credenziali solo locali; errori recuperabili.
- **Test:** unitari con fixture sintetiche per create/update/remove, duplicati, rollback, redazione e migrazione.
- **Vincoli:** nessun segreto versionato o nei log; compatibilita` con i loader e servizi operativi esistenti.
- **Esclusioni:** layout GUI, wizard, monitoraggio e servizi reali.

### V114-T17.2 - Wizard primo avvio

- **Obiettivo:** guidare Cartelle, Caselle, Registro condiviso e Verifica finale.
- **Dipendenze:** V114-T17.1.
- **Ambito:** rilevamento primo avvio, navigazione, validazioni, riepilogo, salvataggio e riapertura.
- **Criteri di accettazione:** nessun YAML/env/Python richiesto; cartelle verificate; almeno due account inseribili; Bucoliche facoltativo; problemi azionabili.
- **Test:** test UI/servizi con filesystem temporaneo e provider fake, inclusi avanti/indietro e configurazione incompleta.
- **Vincoli:** linguaggio utente; nessuna rete automatica; nessun nuovo Spreadsheet o tab.
- **Esclusioni:** CRUD ordinario completo, hardening finale credenziali e monitoraggio continuo.

### V114-T17.3 - Gestione multi-account completa

- **Obiettivo:** gestire l'intero ciclo di vita delle caselle dalla GUI.
- **Dipendenze:** V114-T17.2.
- **Ambito:** tabella, parte semplice/avanzata, add/edit/enable/disable/remove e test IMAP per account.
- **Criteri di accettazione:** due account con host e credenziali distinti persistono; Gmail ha default; generico e` personalizzabile; test separato read-only.
- **Test:** unitari CRUD e UI con almeno due account sintetici, alias duplicati, rimozione e fake IMAP.
- **Vincoli:** accesso prudente `BODY.PEEK`; nessun ack o mutazione remota nel test collegamento.
- **Esclusioni:** vault remoto, import massivo e modifica del form Apps Script.

### V114-T17.4 - Gestione sicura credenziali

- **Obiettivo:** rendere trasparente e sicuro l'intero ciclo delle credenziali locali.
- **Dipendenze:** V114-T17.3.
- **Ambito:** password mascherata, mostra/nascondi, scrittura locale, aggiornamento, cancellazione e redazione.
- **Criteri di accettazione:** credenziali ritrovate dopo riapertura, mai esposte in YAML, log, errori, export o repository; nomi env deterministici senza collisioni.
- **Test:** persistenza temporanea, permessi/errore scrittura, update/remove, scanner di output e controllo file vietati.
- **Vincoli:** `.env` e file locali restano ignorati da Git; nessun secret manager remoto.
- **Esclusioni:** sincronizzazione credenziali tra PC e autenticazione Google live.

### V114-T17.5 - Avvio e arresto non bloccanti

- **Obiettivo:** distinguere controllo singolo e automatico con controllo completo del ciclo di vita.
- **Dipendenze:** V114-T17.4.
- **Ambito:** worker/processo gestito, coda eventi, stato, stop, chiusura finestra e prevenzione doppi avvii.
- **Criteri di accettazione:** GUI reattiva; stop deterministico; stato attivo/fermo/errore; nessun processo orfano.
- **Test:** runner fake lento, start/stop/restart, doppio start, eccezione worker e chiusura finestra.
- **Vincoli:** riusare il runner applicativo; niente processo continuo con `subprocess.run` sul thread principale.
- **Esclusioni:** Task Scheduler e dashboard completa.

### V114-T17.6 - Home operativa

- **Obiettivo:** rendere immediati stato e azioni quotidiane.
- **Dipendenze:** V114-T17.5.
- **Ambito:** stato, ultima/prossima verifica, caselle attive, contatori, problemi e tre azioni primarie.
- **Criteri di accettazione:** stato coerente col worker e aggiornato senza blocchi; azioni principali sempre riconoscibili.
- **Test:** transizioni di stato e contatori con eventi sintetici, inclusi errore e assenza configurazione.
- **Vincoli:** Europe/Rome; niente termini o output CLI nella Home.
- **Esclusioni:** analisi storica avanzata e metriche remote.

### V114-T17.7 - Vista Attivita` leggibile

- **Obiettivo:** mostrare attivita` ed errori in linguaggio comprensibile.
- **Dipendenze:** V114-T17.6.
- **Ambito:** proiezione eventi, tabella e filtri per casella, esito, data ed errore.
- **Criteri di accettazione:** righe con data/ora, casella, messaggio, allegato, azione, esito e problema; filtri combinabili; errori azionabili.
- **Test:** proiezioni e filtri su eventi sintetici, timezone e redazione dati sensibili.
- **Vincoli:** niente JSON grezzo nella vista ordinaria; SQLite resta dettaglio interno.
- **Esclusioni:** dashboard web, analytics remoto e modifica dello schema Registro Google.

### V114-T17.8 - Impostazioni contestuali

- **Obiettivo:** sostituire il pannello globale con impostazioni collocate nel contesto corretto.
- **Dipendenze:** V114-T17.7.
- **Ambito:** Limbo, dati locali, intervallo, scanner, Bucoliche, avvio Windows e impostazioni generali.
- **Criteri di accettazione:** `Parametri azioni` rimosso; nessun campo irrilevante simultaneo; dettagli tecnici confinati alla diagnostica.
- **Test:** visibilita` condizionale, validazioni e persistenza per ciascuna sezione.
- **Vincoli:** una fonte autorevole per dato; parola `staging` assente dall'interfaccia ordinaria.
- **Esclusioni:** nuove preferenze non richieste e redesign del form Apps Script.

### V114-T17.9 - Automazione Windows completa

- **Obiettivo:** amministrare l'avvio automatico interamente dalla GUI.
- **Dipendenze:** V114-T17.8.
- **Ambito:** servizi condivisi per install, query stato/ultimo esito e remove; pannello GUI dedicato.
- **Criteri di accettazione:** stato reale leggibile, installazione/rimozione confermate e nessuna scelta manuale di Python.
- **Test:** comandi Task Scheduler simulati, parsing stato/errori, idempotenza e conferme distruttive.
- **Vincoli:** solo Windows 11 e Utilita` di Pianificazione; niente servizio residente o finestra visibile.
- **Esclusioni:** supporto scheduler di altri sistemi e modifiche al monitoraggio operativo.

### V114-T17.10 - Collaudo utente finale

- **Obiettivo:** dimostrare il percorso completo esclusivamente GUI.
- **Dipendenze:** V114-T17.9 e tutti i task precedenti.
- **Ambito:** installazione/configurazione da zero, due caselle, persistenza, prova sicura, start/stop, attivita`, Windows e manutenzione.
- **Criteri di accettazione:** nessun terminale o editing YAML/`.env`; due account distinti verificabili; riapertura conserva dati; nessun blocco/processo orfano; linguaggio comprensibile.
- **Test:** suite offline completa piu` checklist manuale su profilo di test controllato; documentare esiti e problemi.
- **Vincoli:** niente account o dati reali nei test automatici; nessun `clasp push`; chiusura T17 solo con collaudo positivo.
- **Esclusioni:** nuove funzioni di prodotto oltre il percorso definito.
