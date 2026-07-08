# Backlog di sviluppo

Nota: lo storico, i completamenti chiusi e le milestone finite sono stati spostati in
`docs/DEV_BACKLOG_ARCHIVE.md`; il registro datato e` in `docs/CHANGELOG_DEV.md`.
Le fonti operative leggere restano `docs/CODEX_STATE.md` e `docs/NEXT_CODEX_TASKS.md`.

Stati: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`. Qui restano solo task attivi o bloccati.

## Milestone v1.1.4 - Rifinitura collaudo, setup e hardening

Obiettivo: consolidare collaudo, setup e hardening prima di qualunque rifinitura di UX,
mantenendo task piccoli, seriali, verificabili e doc-first.

Nota operativa: il primo task eseguibile regolare resta `V114-T10 - Setup CLI ready-to-run`.

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
| V114-T12 | TODO | P3 | Reset locale sicuro | `local_connector/`, `README.md`, `docs/SETUP_AND_TEST.md` | esiste `reset-local-state --backup`, con backup automatico, conferma esplicita e messaggi chiari | priorita` bassa; backup obbligatorio; nessuna cancellazione implicita |
| V114-T13 | TODO | P3 | Migrazione installazione locale | `local_connector/`, `README.md`, `docs/SETUP_AND_TEST.md` | export/import configurazione funzionano senza segreti in chiaro e supportano cambio PC o cartelle | priorita` bassa; nessun segreto in chiaro; nessun dato personale |
| V114-T14 | TODO | P2 | Avvio Caronte locale | `local_connector/`, CLI utente finale, `README.md` | esiste un comando unico tipo `virgilio watch` o `virgilio local-watch` che avvia il connettore e resta in attesa controllando la mail | un solo comando utente finale; niente GUI nuova; niente polling fuori controllo |
| V114-T15 | TODO | P3 | Installazione automatica Win11 | `local_connector/`, `README.md`, `docs/SETUP_AND_TEST.md` | esiste un comando per l'esecuzione automatica su Windows 11 tramite Utilita di Pianificazione | solo Windows 11; niente servizi residenti; niente installazioni silenziose ambigue |
| V114-T16 | TODO | P2 | Documentazione utente finale | `README.md`, `docs/SETUP_AND_TEST.md`, `docs/CLASP_WORKFLOW.md` | installazione minima, primo avvio, test, uso quotidiano e troubleshooting sono spiegati in modo operativo | niente segreti, niente termini macchina superflui, niente nuove procedure non testate |
