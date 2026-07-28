# Architettura unificata Virgilio

Virgilio ha due ingressi tecnici e un solo flusso operativo.

Frase guida: "Virgilio ha due ingressi tecnici e un solo flusso operativo."

Questo documento e` l'unica fonte canonica dell'architettura corrente. README,
AGENTS, runbook e backlog rimandano qui; i documenti architetturali precedenti
sono fonti storiche e non introducono decisioni concorrenti.

Baseline descritta: Virgilio `1.1.0`, commit funzionale collaudato `7e18277`,
collaudo umano `PASS` del 2026-07-28 e Apps Script deployment `40`.

## Flusso unico

Acquisizione -> Quarantena locale eventuale -> Limbo Drive unico -> Da archiviare -> Form -> Pratica finale -> Registro

Il documento e` l'unita` del flusso. `Da archiviare` contiene una riga per
documento, mentre una mail e` completata soltanto quando tutti i documenti
correlati risultano `archiviato`. Il profilo locale puo` aggiungere l'etichetta
di completamento e rimuovere la sola etichetta di ingresso dopo aver verificato
la post-condizione, senza `DELETE`, `MOVE` o `EXPUNGE`.

## Confini dei componenti

```text
GmailApp ---------------------> Apps Script ----+
IMAP -> quarantena -> scan -> servizi locali ---+-> Limbo -> Da archiviare
                                                  -> Form -> pratica -> Registro

user_app ---------+
maintenance_gui --+-> servizi applicativi condivisi -> dominio/porte -> adapter
CLI ---------------+
```

- Apps Script e` l'adattatore del profilo Google-only e conserva form, coda,
  archiviazione e integrazioni Google; non viene sostituito da Python.
- Il Local connector acquisisce da IMAP, applica i gate locali e coordina gli
  adapter Drive, Registro e completamento senza inviare byte, base64 o path
  locali ad Apps Script.
- Il Limbo Drive, `Da archiviare`, il Form, la pratica finale e il Registro sono
  risorse condivise del flusso, non implementazioni alternative per profilo.
- SQLite conserva stato tecnico locale, ripresa e correlazioni del connettore;
  non sostituisce il Registro umano cloud e non e` esposto nella UX ordinaria.
- Bucoliche e` il contratto append-only del Registro condiviso, non un database
  applicativo parallelo.

## Profili operativi

Questa e` la distinzione da usare prima di aprire un task o una branch.
Dopo il collaudo, il profilo da usare resta quello coerente con la superficie del lavoro: Google-only per Apps Script e Google Workspace; Local connector per attivita` locali, offline e di test.

### Google-only

- Ingresso tecnico: `GmailApp`.
- E` mono-account: usa una sola casella alla volta.
- Usa il Limbo Drive condiviso unico come prima area operativa visibile in Google Drive.
- Crea una riga in `Da archiviare` quando il documento e` pronto per la decisione umana.
- E` il profilo da usare quando il task resta dentro Google Workspace, Apps Script e `clasp`.
- Rimane il profilo semplice per chi lavora solo in Google Workspace.

### Local connector

- Ingresso tecnico: `IMAP locale`.
- Puo` leggere una o piu` caselle, inclusa una casella Google Workspace via IMAP.
- Gli esempi di configurazione mostrano almeno due account generici con alias neutri.
- Passa prima da `Quarantena locale`, poi da `Scan`, poi nel Limbo Drive unico.
- Gli allegati Office (`.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`) entrano solo con scansione obbligatoria; macro-enabled, archivi compressi ed eseguibili restano bloccati.
- Produce gli stessi oggetti operativi del profilo Google-only.
- E` il profilo da usare quando il task deve restare offline, usare fixture e verifiche locali.
- Rimane il profilo piu` sicuro per piu` caselle, piu` utenti e per la scansione prima del Limbo.

## Classificazione moduli

| Profilo | Moduli canonici | Snapshot / supporto | Nota |
|---|---|---|---|
| Google-only | `apps_script/src/*.gs`, `apps_script/src/virgilio.html`, `apps_script/src/appsscript.json` | `.clasp.json`, `clasp` CLI | la sorgente canonica e` in `apps_script/src`; `clasp` sincronizza direttamente quella cartella |
| Local connector | `local_connector/src/virgilio_connector/*.py` | `local_connector/tests/`, `local_connector/tests/fixtures/`, `scripts/dev/` | resta locale, offline e testabile senza servizi reali |

## Presentazioni e servizi condivisi

Le sole presentazioni desktop target sono `virgilio_connector.user_app` per
`Caronte` e `virgilio_connector.maintenance_gui` per `Caronte Manutenzione`.
La CLI in `virgilio_connector.__main__` e` un terzo adapter degli stessi servizi.

| Superficie | Responsabilita` | Non possiede |
|---|---|---|
| `user_app` | primo avvio, Home, caselle, attivita` e impostazioni in linguaggio utente | regole operative, output CLI grezzo o dettagli tecnici |
| `maintenance_gui` | configurazione tecnica, diagnostica, backup, integrita` e reset controllato | flusso ordinario o implementazione GUI legacy |
| CLI | parsing, dispatch, output e codici di ritorno per sviluppo e automazione | copie dei casi d'uso |
| servizi `application` | configurazione, account, operazioni, attivita`, manutenzione e avvio Windows | widget, toolkit grafici o parsing CLI |
| dominio, porte e adapter | invarianti e accessi concreti a filesystem, credenziali, mail, Drive e Registro | navigazione e decisioni di presentazione |

Le dipendenze procedono dalle tre superfici verso i servizi, quindi verso
dominio/porte e adapter. I servizi non importano presentazioni o `__main__`.
`user_app` e `maintenance_gui` non importano `gui` o `gui_*`: questi moduli sono
legacy abbandonato, non sono target di sviluppo o packaging e saranno rimossi
solo dal task di pulizia dedicato.

I risultati dei servizi sono strutturati e gli errori sono tipizzati: la GUI
utente li traduce in indicazioni azionabili, Manutenzione espone il dettaglio
tecnico pertinente e la CLI sceglie testo e return code, senza duplicare la
regola operativa. Il controllo continuo e` coordinato da un runner non
bloccante, con esclusione dei doppi avvii e arresto controllato.

## Lessico ufficiale

- Quarantena: cartella locale non condivisa, prima della scansione.
- Limbo: unica cartella Google Drive condivisa dei documenti acquisiti ma non ancora archiviati.
- Da archiviare: coda operativa umana dei documenti nel Limbo.
- Registro: unico registro di audit.
- Form: interfaccia umana Virgilio.
- Pratica finale: cartella della commessa/pratica, con archiviazione in `02_corrispondenza` o cartella equivalente.

## Mappa termini legacy -> ufficiali

| Termine legacy | Termine ufficiale o uso corretto | Nota |
|---|---|---|
| `staging` | `Limbo` | termine tecnico storico; non usarlo nella UX |
| `Virgilio_Inbox` | `Da archiviare` | nome tecnico della coda operativa |
| `Bucoliche_Eventi`, `Bucoliche_Stato`, `Bucoliche_Conflitti` | nomi tecnici storici | non sono registri cloud attivi; stato e conflitti restano proiezioni locali |
| `manifest` | dettaglio diagnostico | resta nel bridge e nei controlli tecnici |
| `fingerprint` | dettaglio diagnostico | non esporre nella UX normale |
| `SQLite` | registro operativo locale del connettore | solo nel profilo local connector, non nella UX utente |

## Ruoli

### Registro

Il Registro e` l'unico audit ufficiale. Contiene gli eventi rilevanti, gli esiti e le tracce operative necessarie a ricostruire cosa e` successo.
Nel profilo Google-only, `registraErrore()` e `registraConflitto()` sono gli hook operativi che traducono errori e conflitti in eventi di audit leggibili.
Il tab cloud canonico e` `bucoliche`, con lo schema umano storico a 17 colonne.
Google-only e Local connector appendono nello stesso tab e rispettano le stesse
regole. Le proiezioni tecniche di stato/conflitto restano locali e non generano
copie parallele nel foglio Google.

### Schema minimo del Registro

Il Registro resta append-only e usa una riga per ogni evento osservabile. Ogni riga contiene almeno:

- `registro_id`: identificativo univoco dell'evento.
- `timestamp`: momento dell'evento in ora locale `Europe/Rome`.
- `ingresso`: `Google-only` oppure `Local connector`.
- `fase`: fase del flusso, per esempio `acquisizione`, `limbo`, `da archiviare`, `form`, `pratica finale`, `errore`, `conflitto`.
- `oggetto`: riferimento operativo principale, per esempio `inbox_id`, `message_id`, `drive_file_id`, `fingerprint` o `pratica_id`.
- `esito`: `ok`, `attesa_umano`, `archiviato`, `bloccato`, `errore`, `conflitto`.
- `nota`: sintesi breve, leggibile e non ambigua.
- `correlazioni_tecniche`: campo opzionale per compatibilita` e diagnostica.

Tutti i timestamp operativi restano in ora locale `Europe/Rome`; non si introducono campi UTC o copie tecniche parallele.

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
| Test e harness | `testVirgilioSenzaDeploy()`, `testVirgilioInboxSchema()`, `testCaronteInboxArchiviazione()`, `testBucolicheRegistroEventi()`, `testDriveStagingCloudVerify()`, `testNotificheArchiviazioneInbox()` | suite `pytest`, fixture sintetiche e smoke sotto `scripts/dev/` | non perdere i test che proteggono il contratto |

## Cosa resta tecnico o legacy

- `staging` resta un termine tecnico storico e non deve comparire nella UX.
- `Bucoliche_Eventi`, `Bucoliche_Stato` e `Bucoliche_Conflitti` sono nomi storici:
  non vengono creati o alimentati come tab cloud paralleli.
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
