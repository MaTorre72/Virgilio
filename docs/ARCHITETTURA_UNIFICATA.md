# Architettura unificata Virgilio

Virgilio ha due ingressi tecnici e un solo flusso operativo.

Frase guida: "Virgilio ha due ingressi tecnici e un solo flusso operativo."

Questo documento e` il riferimento condiviso per lessico, ruoli e flusso operativo.
README, AGENTS e backlog rimandano qui quando serve allineare il modello comune.

## Flusso unico

Acquisizione -> Limbo -> Da archiviare -> Form -> Pratica finale -> Registro

## Profili operativi

### Google-only

- Ingresso tecnico: `GmailApp`.
- Usa il Limbo condiviso come prima area operativa visibile in Google Drive.
- Crea una riga in `Da archiviare` quando il documento e` pronto per la decisione umana.
- Rimane il profilo semplice per chi lavora solo in Google Workspace.

### Local connector

- Ingresso tecnico: `IMAP locale`.
- Passa prima da `Quarantena`, poi da `Scan`, poi nel Limbo.
- Produce gli stessi oggetti operativi del profilo Google-only.
- Rimane il profilo piu` sicuro per piu` caselle, piu` utenti e per la scansione prima del Limbo.

## Classificazione moduli

| Profilo | Moduli canonici | Snapshot / supporto | Nota |
|---|---|---|---|
| Google-only | `apps_script/src/*.gs`, `apps_script/src/virgilio.html` | `apps_script/clasp/*.js`, `apps_script/clasp/virgilio.html`, `apps_script/clasp/appsscript.json` | la sorgente canonica e` in `apps_script/src`; `clasp` e` solo mirror di sincronizzazione |
| Local connector | `local_connector/src/virgilio_connector/*.py` | `local_connector/tests/`, `local_connector/tests/fixtures/`, `local_connector/scripts/` | resta locale, offline e testabile senza servizi reali |

## Lessico ufficiale

- Quarantena: cartella locale non condivisa, prima della scansione.
- Limbo: cartella Google Drive condivisa dei documenti acquisiti ma non ancora archiviati.
- Da archiviare: coda operativa umana dei documenti nel Limbo.
- Registro: unico registro di audit.
- Form: interfaccia umana Virgilio.
- Pratica finale: cartella della commessa/pratica, con archiviazione in `02_corrispondenza` o cartella equivalente.

## Mappa termini legacy -> ufficiali

| Termine legacy | Termine ufficiale o uso corretto | Nota |
|---|---|---|
| `staging` | `Limbo` | termine tecnico storico; non usarlo nella UX |
| `Virgilio_Inbox` | `Da archiviare` | nome tecnico della coda operativa |
| `Bucoliche_Eventi`, `Bucoliche_Stato`, `Bucoliche_Conflitti` | supporti tecnici del `Registro` | restano compatibilita` tecnica, non inbox |
| `manifest` | dettaglio diagnostico | resta nel bridge e nei controlli tecnici |
| `fingerprint` | dettaglio diagnostico | non esporre nella UX normale |
| `SQLite` | registro operativo locale del connettore | solo nel profilo local connector, non nella UX utente |

## Ruoli

### Registro

Il Registro e` l'unico audit ufficiale. Contiene gli eventi rilevanti, gli esiti e le tracce operative necessarie a ricostruire cosa e` successo.
Nel profilo Google-only, `registraErrore()` e `registraConflitto()` sono gli hook operativi che traducono errori e conflitti in eventi di audit leggibili.

### Schema minimo del Registro

Il Registro resta append-only e usa una riga per ogni evento osservabile. Ogni riga contiene almeno:

- `registro_id`: identificativo univoco dell'evento.
- `timestamp_utc`: momento dell'evento in UTC.
- `ingresso`: `Google-only` oppure `Local connector`.
- `fase`: fase del flusso, per esempio `acquisizione`, `limbo`, `da archiviare`, `form`, `pratica finale`, `errore`, `conflitto`.
- `oggetto`: riferimento operativo principale, per esempio `inbox_id`, `message_id`, `drive_file_id`, `fingerprint` o `pratica_id`.
- `esito`: `ok`, `attesa_umano`, `archiviato`, `bloccato`, `errore`, `conflitto`.
- `nota`: sintesi breve, leggibile e non ambigua.
- `correlazioni_tecniche`: campo opzionale per compatibilita` e diagnostica.

Gli eventi tecnici storici possono alimentare questo schema, ma non diventano nuovi registri produttivi separati.

### Da archiviare

`Da archiviare` e` la coda di lavoro corrente. Non e` un archivio storico e non sostituisce il Registro.
Serve a rappresentare le pratiche che richiedono una decisione o un completamento umano.

Schema minimo del record:

- una riga per documento nel Limbo;
- una sola riga attiva per `fingerprint` o, se manca, `attachment_id`;
- il flusso normale e` `da_lavorare -> in_lavorazione -> archiviato`;
- `notes` raccoglie metadati compatti `chiave=valore`, non un secondo archivio.

| Gruppo | Campi | Regola |
|---|---|---|
| Identita` riga | `inbox_id`, `created_at`, `status` | sempre presenti; `status` parte da `da_lavorare` |
| Identita` tecnica | `fingerprint` o `attachment_id`, `sha256`, `drive_file_id`, `manifest_file_id` | almeno una chiave tecnica piu` gli ID Drive/manifest verificati |
| Provenienza | `command_id`, `account_alias`, `source_email`, `source_message_id`, `source_message_uid`, `source_subject`, `source_sender`, `original_filename`, `staged_filename` | metadati di tracciamento del documento |
| Interazione umana | `suggested_cliente`, `suggested_sito`, `suggested_pratica`, `form_url` | possono essere valorizzati dal form o restare vuoti fino alla presa in carico |
| Note | `notes` | metadati compatti `chiave=valore`, usati per stati e correlazioni |

Stati ammessi:

- `da_lavorare`: documento pronto per la decisione umana.
- `in_lavorazione`: il record e` stato aperto o collegato al form.
- `archiviato`: il file e` stato trasferito nella pratica finale.

`Virgilio_Inbox` resta il nome tecnico del tab, `Da archiviare` e` il nome utente della coda, e il Registro resta l'unico audit storico.

## Funzioni da preservare

Questa mappa non e` un inventario completo di helper interni. Serve a indicare le superfici che vanno
riconciliate senza perdita di comportamento quando la sorgente canonica Apps Script resta separata
dallo snapshot `clasp`.

| Dominio | Google-only da preservare | Local connector da preservare | Nota di riconciliazione |
|---|---|---|---|
| Ingresso web e form | `doGet(e)`, `doPost(e)`, `apriPraticaDaVirgilio(dati)`, `renderInboxContext()`, `applyInboxSuggestions()`, `buildRiepilogo()`, `apri()` | `main()` e i subcommand CLI di `__main__.py` | il form resta unico e non va riscritto in modo invasivo |
| Coda `Da archiviare` | `caronteGetVirgilioInboxSchema()`, `caronteSetupVirgilioInbox()`, `caronteRegistraVirgilioInbox()`, `caronteCollegaSubmitVirgilioInbox()`, `caronteGetVirgilioInboxForForm()`, `caronteArchiviaVirgilioInbox()` | `DriveStagingVerifyClient.verify_manifest()`, `DriveStagingIntakeTestClient.intake_manifest()`, `DaArchiviareIntakeHttpClient.create_record()`, `build_da_archiviare_intake_payload()` | stesso contratto metadata-only, nessun byte o path locale |
| Acquisizione e scan | `caronteTraghetta()`, `_processaMailUtente(utente)`, `_salvaAllegatoInLimbo()`, `èAllegatoReale(allegato)` | `MultiAccountReadonlyScanner`, `MultiAccountImapProcessor`, `LocalDriveStagingTransport` | preservare i gate e l'idempotenza dei passaggi |
| Setup e diagnostica | `caronteSetupTrigger()`, `caronteStopTrigger()`, `caronteStatoTrigger()`, `caronteSetupCredenziali()`, `generaToken()`, `caronteStatoConfigurazione()`, `caronteStatoCredenziali()` | `doctor`, `pilot-check`, `pilot-preview`, `pilot-run`, `init-config` | entrambi devono restare verificabili in dry-run |
| Audit e notifiche | `registraSuBucoliche()`, `aggiornaRigheAllegati()`, `registraErrore()`, `registraConflitto()`, `avvisaTeam()`, `avvisaArchiviazioneVirgilioInbox()`, `avvisaChat()`, `avvisaTelegram()` | `BucolicheAppendOnlyAdapter`, `LocalConflictChecker`, `audit_entry()`, `export_central_events()`, `export_registro_events()` | l'audit ufficiale resta unico; il resto e` tecnico |
| Test e harness | `testVirgilioSenzaDeploy()`, `testVirgilioInboxSchema()`, `testCaronteInboxArchiviazione()`, `testBucolicheRegistroEventi()`, `testDriveStagingCloudVerify()`, `testNotificheArchiviazioneInbox()` | suite `pytest`, fixture sintetiche, `compare_parser_fixtures()`, `extract_local_fixtures()` | non perdere i test che proteggono il contratto |

## Cosa resta tecnico o legacy

- `staging` resta un termine tecnico storico e non deve comparire nella UX.
- `Bucoliche_Eventi`, `Bucoliche_Stato` e `Bucoliche_Conflitti` restano supporti tecnici o di compatibilita`.
- `Virgilio_Inbox` resta il nome tecnico della coda operativa; nella UX si chiama `Da archiviare`.
- `manifest`, `fingerprint` e `SQLite` restano dettagli diagnostici.

## Cosa non fare

- Non introdurre un secondo Limbo operativo.
- Non creare nuovi registri produttivi separati dal Registro.
- Non usare `Bucoliche_*` come inbox o come coda utente.
- Non mandare byte, base64 o path locali ad Apps Script.
- Non riscrivere il form per separare i due profili.
- Non sostituire Apps Script con Python.
- Non esporre dettagli macchina inutili nella UX normale.

## Nota operativa

Gli sviluppi gia` fatti su Google Apps Script e sul local connector vanno riconciliati, non cancellati. Le parti tecniche storiche si preservano finche` servono alla compatibilita` o alla diagnostica.
