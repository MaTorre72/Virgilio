# AGENTS.md - Virgilio

## Missione

Virgilio acquisisce documenti da email, li porta nel Limbo, li mette nella lista Da archiviare,
raccoglie la decisione umana tramite form e li archivia nella pratica finale, registrando tutto
nel Registro.

## Architettura

Virgilio ha due ingressi tecnici e un solo flusso operativo.

Ingressi:

- Google-only: `GmailApp -> Limbo -> Da archiviare -> Form -> Pratica finale -> Registro`
- Local connector: `IMAP locale -> Quarantena -> Scan -> Limbo -> Da archiviare -> Form -> Pratica finale -> Registro`

Regole architetturali vincolanti:

- Esiste un solo Limbo operativo; `staging` e` legacy tecnico e non va usato nella UX.
- Esiste un solo Registro di audit ufficiale.
- `Bucoliche_Eventi`, `Bucoliche_Stato` e `Bucoliche_Conflitti` restano compatibilita` tecnica, non nuovi registri produttivi.
- `Virgilio_Inbox` e` la coda operativa; nella documentazione utente si chiama `Da archiviare`.
- `Form` resta unico e funziona sia con che senza `inbox_id`.
- Il bridge verso Apps Script usa solo metadati e file gia` visibili in Google Drive.
- Nessun byte, base64 o path locale va inviato ad Apps Script.
- Il codice storico si preserva e si riconcilia; non si sovrascrive alla cieca.

## Lessico ufficiale

- Quarantena: cartella locale non condivisa, prima della scansione.
- Limbo: cartella Google Drive condivisa dei documenti acquisiti ma non ancora archiviati.
- Da archiviare: coda operativa umana dei documenti nel Limbo.
- Registro: unico registro di audit.
- Form: interfaccia umana Virgilio.
- Pratica finale: cartella della commessa/pratica, con archiviazione in `02_corrispondenza` o cartella equivalente.

Lessico da evitare nella documentazione utente:

- staging
- Bucoliche_Eventi
- Bucoliche_Stato
- Bucoliche_Conflitti
- fingerprint
- manifest
- SQLite

## Regole di sicurezza

- Non modificare `main`.
- Non leggere, alterare o archiviare mail reali senza autorizzazione esplicita.
- Non chiamare Google reale nei test.
- Non versionare segreti, token, password, `.env`, `.env.*`, `.local_data/`, `.secrets/`, `_staging/` o `.clasprc.json`.
- Preferire cambi piccoli, reversibili e coperti da test.
- Mantenere dry-run e fake client per storage, email e Google.
- Fermarsi se il working tree e` sporco per modifiche non spiegate o se serve una scelta irreversibile.

## Workflow Git

- Verificare branch e `git status --short` prima di modificare file.
- Lavorare sulla branch `codex/v1.1-development` o su una branch dedicata derivata da essa.
- Tenere un task per ciclo e un commit per task.
- Commit in italiano con forma `<tipo>: <azione breve>` (`feat`, `fix`, `test`, `docs`, `chore`).
- Non committare file segreti o output effimeri.
- Non fare merge o reset distruttivi.

## Workflow clasp

- Prima di ogni attivita` Apps Script verificare `node -v`, `npm -v` e `clasp --version`.
- Se `clasp` manca, proporre `npm install -g @google/clasp`.
- Prima di lavorare su Apps Script verificare il login `clasp`; se manca, fermarsi e chiedere all'utente di eseguire `clasp login`.
- Lavorare sul progetto reale collegato, non su copie casuali.
- Verificare la presenza di `.clasp.json` prima di modificare Apps Script.
- Eseguire `clasp pull` prima di ogni modifica Apps Script.
- Non fare `clasp push` senza richiesta esplicita o task dedicato.
- Non committare `.clasprc.json`.

## Regole di modifica Apps Script

- Creare una branch dedicata prima di ogni modifica.
- Non sovrascrivere codice live senza `clasp pull` e revisione del diff.
- Se `clasp push` e` previsto, mostrare prima file modificati, diff sintetico, rischio e comando.
- Non introdurre credenziali manuali o workaround per il login.
- Non toccare file segreti o cartelle vietate.

## Regole di modifica local connector

- Restare locali e offline per test e diagnosi.
- Usare fake client, fixture e dry-run.
- Non chiamare Gmail reale, Drive reale o Google reale.
- Non introdurre AI, RAG, nuovi server web o database remoti.
- Mantenere separati profili Google-only e local connector.

## Regole di test

- Leggere `docs/DEV_BACKLOG.md` e `docs/DEFINITION_OF_DONE.md` prima di scegliere il task.
- Dopo modifiche documentali, verificare solo i file creati o aggiornati.
- Se si tocca codice, aggiungere test mirati prima dello smoke.
- Eseguire `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1` quando il task tocca il percorso locale o la governance di sviluppo.
- Non usare servizi reali nei test.

## Criteri di completamento

- Il task del backlog e` soddisfatto.
- La documentazione minima e il backlog sono allineati.
- I test richiesti dal task sono verdi.
- Il smoke locale e` verde quando applicabile.
- Nessun segreto o dato operativo e` stato tracciato.
- Il commit e` atomico, leggibile e la working tree e` pulita.

## Vietato

- Modificare `main`.
- Usare real mail o Google reale senza autorizzazione.
- Committare segreti, token, password o `.clasprc.json`.
- Usare `staging` come lessico utente finale.
- Trattare `Bucoliche_*` come nuovi registri produttivi.
- Fare deploy o `clasp push` senza richiesta esplicita.
- Riscrivere il form o sostituire Apps Script con Python.
