# Virgilio v1.1.2 - Ricognizione 1.0 e roadmap di integrazione Caronte -> Virgilio

## 1. Sintesi decisionale

La scelta di usare Google Apps Script per la parte Virgilio v1.1 e` valida nel perimetro attuale: il repo contiene gia` form HTML, menu Sheets, notifiche Chat/Telegram, anagrafiche e creazione pratiche su Drive.

La decisione ancora aperta non e` "Google o non Google", ma se il ponte tra Caronte Locale e Virgilio 1.0 debba restare temporaneo oppure diventare l'interfaccia stabile verso Google Workspace.

Decisione pratica di questa fase:

- non riscrivere il form;
- non sostituire Apps Script con Python;
- non introdurre AI, RAG, database remoti o server web;
- tenere Caronte Locale come motore tecnico e Virgilio come punto umano/Google finale;
- usare un bridge metadata-only, non un trasporto di byte.

### Regola architetturale centrale

`Bucoliche_Eventi`, `Bucoliche_Stato` e `Bucoliche_Conflitti` non sono il punto di ingresso umano del processo Virgilio.

Sono registri tecnici:
- `Bucoliche_Eventi` registra ciò che Caronte ha fatto;
- `Bucoliche_Stato` sintetizza lo stato corrente degli allegati/fingerprint;
- `Bucoliche_Conflitti` evidenzia anomalie tecniche o duplicazioni.

Il punto di ingresso umano/applicativo deve essere `Virgilio_Inbox`.

`Virgilio_Inbox` rappresenta la coda dei documenti acquisiti tecnicamente da Caronte e pronti per una decisione umana: scelta cliente, sito, pratica, responsabile, destinazione finale e conferma di archiviazione.

Conseguenza pratica:
- Bucoliche resta registro/audit;
- Virgilio_Inbox diventa la coda operativa;
- il form Virgilio lavora sui record di Virgilio_Inbox, non direttamente su Bucoliche_Eventi o Bucoliche_Stato.

## 2. Cosa esiste gia` in Virgilio 1.0

### 2.1 Inventario codice Google Apps Script

| File | Funzione | Scopo | Input | Output | Dipendenze | Riutilizzabile | Note |
|---|---|---|---|---|---|---|---|
| `webapp.gs` | `doGet` | Entry point della Web App | HTTP GET | `HtmlOutput` del form | `HtmlService`, `_creaOutputVirgilio_` | Si | Serve sia Web App sia dialog interno Sheets |
| `webapp.gs` | `_creaOutputVirgilio_` | Istanzia il template HTML | template `virgilio.html` | HTML pronto | `HtmlService`, `_creaDataUriImmagine_`, `DriveApp` | Si | Inietta il logo come data URI |
| `webapp.gs` | `_creaDataUriImmagine_` | Legge immagine da Drive e la converte | `fileId` logo | `data:` URI | `DriveApp`, `Utilities` | Si | Richiede file immagine valido |
| `setup.gs` | `caronteSetupTrigger` | Crea trigger temporale ogni 5 minuti | nessuno | trigger creato | `ScriptApp`, `Logger` | Si | Rimuove duplicati prima di creare |
| `setup.gs` | `caronteStopTrigger` | Ferma i trigger di Caronte | nessuno | trigger rimossi | `ScriptApp`, `Logger` | Si | Pausa operativa |
| `setup.gs` | `caronteStatoTrigger` | Elenca i trigger attivi | nessuno | log diagnostico | `ScriptApp`, `Logger` | Si | Solo diagnostica |
| `setup.gs` | `onOpen` | Menu Sheets "Virgilio" | apertura spreadsheet | menu UI | `SpreadsheetApp`, `testVirgilioSenzaDeploy`, `testGmailDaTraghettare` | Si | Fallisce in progetto standalone senza bloccare |
| `setup.gs` | `mostraVirgilio` | Apre il form in dialog modal | nessuno | finestra dialog | `SpreadsheetApp`, `_creaOutputVirgilio_` | Si | Entry point umano interno |
| `setup.gs` | `caronteSetupCredenziali` | Scrive segnaposto nelle Script Properties | nessuno | credenziali placeholder | `PropertiesService`, `Logger` | Si | Solo setup manuale |
| `setup.gs` | `generaToken` | Genera token per `VIRGILIO_TOKEN` | nessuno | token in log | `Utilities`, `Logger` | Si | Da copiare in setup credenziali |
| `setup.gs` | `caronteStatoCredenziali` | Mostra lo stato delle props | nessuno | log diagnostico | `PropertiesService`, `Logger` | Si | Non stampa valori |
| `setup.gs` | `caronteResetCredenziali` | Rimuove tutte le props | nessuno | props cancellate | `PropertiesService`, `Logger` | Si | Da usare solo per rotazione completa |
| `caronte.gs` | `doPost` | Endpoint webhook principale | JSON POST | JSON risposta | `ContentService`, `PropertiesService`, `DriveApp`, `GmailApp`, `notifiche.gs`, `bucoliche.gs` | Si | Gestisce anche i rami dry-run locali |
| `caronte.gs` | `apriPraticaDaVirgilio` | Bridge interno senza deploy pubblico | dati form | risposta JSON parsata | `doPost`, `CONFIG` | Si | Simula la Web App dal dialog |
| `caronte.gs` | `testVirgilioSenzaDeploy` | Test server-side del form | dati finti | log + eccezione se fallisce | `apriPraticaDaVirgilio` | Si | Utile per smoke manuale |
| `caronte.gs` | `creaCartellaPratica` | Crea cliente/sito/pratica su Drive | cliente, sito, anno, pratica | `{id,url}` | `DriveApp`, `_trovaOCrea`, `_assicuraStrutturaTrasversaleSito` | Si | Cuore dell'archiviazione finale |
| `caronte.gs` | `_assicuraStrutturaTrasversaleSito` | Copia sottocartelle da Adamo o fallback | `cartellaSito` | struttura pronta | `DriveApp`, `_trovaOCrea` | Si | Riusa Adamo se disponibile |
| `caronte.gs` | `caronteTraghetta` | Polling Gmail ogni 5 minuti | utenti configurati | conteggio allegati | `GmailApp`, `_processaMailUtente`, `registraErrore` | Si | Motore email storico v1.0 |
| `caronte.gs` | `_processaMailUtente` | Estrae allegati da thread etichettati | utente | numero allegati salvati | `GmailApp`, `_apriLimbo`, `_salvaAllegatoInLimbo`, `registraSuBucoliche`, `_avvisaTraghettamento` | Si | Filtra e notifica |
| `caronte.gs` | `_avvisaTraghettamento` | Notifica riepilogo del traghettamento | totale, dettagliMail | avviso team | `avvisaTraghettamentoTeam` | Si | Wrapper non bloccante |
| `caronte.gs` | `_salvaAllegatoInLimbo` | Salva file nel Limbo Drive | allegato, messaggio, limbo | file Drive ID | `DriveApp`, `Utilities`, `_estraiDominio`, `_sanitizzaNomeFile` | Si | Nome file: data_dominio_messageid_originale |
| `caronte.gs` | `èAllegatoReale` | Filtro allegati non utili | allegato | boolean | `GmailAttachment` | Si | Scarta firme, immagini piccole, p7s |
| `caronte.gs` | `_rimuoviEtichetta` | Rimuove etichetta Gmail | thread, etichetta | effetto Gmail | `GmailApp` | Si | Fail silenzioso |
| `caronte.gs` | `_aggiungiEtichetta` | Aggiunge o crea etichetta Gmail | thread, etichetta | effetto Gmail | `GmailApp` | Si | Crea etichetta se manca |
| `caronte.gs` | `_trovaOCrea` | Helper Drive generico | folder, nome | cartella Drive | `DriveApp` | Si | Riutilizzabile ovunque |
| `caronte.gs` | `_trovaCartellaCorrispondenza` | Risale alla cartella sito e trova/crea `02_corrispondenza` | ID pratica | cartella `02_corrispondenza` | `DriveApp`, `_trovaOCrea` | Si | Chiude il ponte Limbo -> pratica |
| `caronte.gs` | `_apriLimbo` | Apre il Limbo | nessuno | folder Limbo | `DriveApp`, `CONFIG` | Si | Errore bloccante se assente |
| `caronte.gs` | `_estraiDominio` | Estrae dominio mittente | stringa mittente | dominio | regex | Si | Serve per naming e log |
| `caronte.gs` | `_rispostaJSON` | Serializza risposta JSON | oggetto | `TextOutput` JSON | `ContentService` | Si | Helper endpoint |
| `caronte.gs` | `_sanitizzaNomeFile` | Sanitizza nome allegato | nome file | nome sicuro | regex | Si | Previene path traversal/naming illegale |
| `caronte.gs` | `_spostaAllegatiDalLimbo` | Sposta file recenti dal Limbo alla corrispondenza | cliente, sito, pratica ID | `{count,fileIds}` | `DriveApp`, `_trovaCartellaCorrispondenza` | Si | Matching temporale, non semantico |
| `caronte.gs` | `_validaLunghezze` | Limita dimensione campi form | dati | errore o ok | nessuna esterna | Si | Protezione log e nomi Drive |
| `caronte.gs` | `_verificaRateLimit` | Rate limit su doPost | nessuno | errore o ok | `CacheService` | Si | 1 richiesta ogni 10 secondi |
| `bucoliche.gs` | `registraSuBucoliche` | Append di una riga evento | oggetto riga | riga scritta | `SpreadsheetApp`, `_aprifoglioBucoliche`, `_timestampLocale` | Si | Schema 17 colonne |
| `bucoliche.gs` | `aggiornaRigheAllegati` | Aggiorna righe `gmail_staging` a `gmail_archiviato` | fileIds + dati pratica | numero righe aggiornate | `SpreadsheetApp` | Si | Riscrive il range in memoria |
| `bucoliche.gs` | `registraErrore` | Scrive errore su Bucoliche | origine, messaggio, contesto | riga errore colorata | `SpreadsheetApp`, `_aprifoglioBucoliche` | Si | Non rilancia l'errore |
| `bucoliche.gs` | `_aprifoglioBucoliche` | Apre o crea il tab `bucoliche` | nessuno | sheet | `SpreadsheetApp`, `CONFIG` | Si | Tab operativo storico |
| `bucoliche.gs` | `_assicuraIntestazione` | Crea header del tab `bucoliche` | sheet | header + formattazione | `SpreadsheetApp` | Si | 17 colonne |
| `bucoliche.gs` | `_timestampLocale` | Timestamp Europe/Rome | nessuno | stringa timestamp | `Utilities` | Si | Formato `yyyy-MM-dd HH:mm:ss` |
| `anagrafiche.gs` | `getAnagraficaVirgilio` | Restituisce anagrafica al form | nessuno | `{clienti,siti,team,tipiPratica}` | `SpreadsheetApp`, helper lettura | Si | Chiamata da `virgilio.html` |
| `anagrafiche.gs` | `aggiungiClienteSito` | Appende una coppia cliente/sito | cliente, sito | effetto sul tab | `SpreadsheetApp`, `_getFoglioAnagrafica` | Si | Idempotente |
| `anagrafiche.gs` | `inizializzaAnagrafica` | Crea i tre tab anagrafici | nessuno | tab pronti | `SpreadsheetApp` | Si | Setup una tantum |
| `anagrafiche.gs` | `_leggiClienti` | Legge i clienti attivi | spreadsheet | array clienti | `SpreadsheetApp` | Si | Deduplica con `Set` |
| `anagrafiche.gs` | `_leggiSiti` | Legge i siti per cliente | spreadsheet | mappa cliente -> siti | `SpreadsheetApp` | Si | Usata per `datalist` HTML |
| `anagrafiche.gs` | `_leggiTeam` | Legge i tecnici attivi | spreadsheet | array oggetti team | `SpreadsheetApp` | Si | Nome, email, ruolo |
| `anagrafiche.gs` | `_leggiTipiPratica` | Legge il vocabolario pratiche | spreadsheet | array oggetti | `SpreadsheetApp` | Si | Specchio del form |
| `anagrafiche.gs` | `_getFoglioAnagrafica` | Helper tab lookup | spreadsheet, nome tab | sheet | `SpreadsheetApp` | Si | Errore se tab mancante |
| `anagrafiche.gs` | `_assicuraTabClientiSiti` | Crea intestazione tab clienti/siti | spreadsheet | tab pronto | `SpreadsheetApp` | Si | Header: cliente, sito, attivo, data_inserimento |
| `anagrafiche.gs` | `_assicuraTabTeam` | Crea intestazione e righe default team | spreadsheet | tab pronto | `SpreadsheetApp` | Si | Popola default Marco, Giulia, Francesco, Sara, Luca |
| `anagrafiche.gs` | `_assicuraTabTipiPratica` | Crea intestazione e vocabolario pratiche | spreadsheet | tab pronto | `SpreadsheetApp` | Si | Include AUA, AIA, VIA, EoW, TR, bonifica, emissioni, rifiuti, sottoprodotti, PEI, PEE, reportAIA, assistenza |
| `anagrafiche.gs` | `_formattaIntestazioneAnagrafica` | Formatta header anagrafico | sheet, numero colonne | stile | `SpreadsheetApp` | Si | Riutilizzabile |
| `notifiche.gs` | `avvisaTeam` | Orchestratore notifiche post-creazione pratica | dati pratica + url | Chat + Telegram | `avvisaChat`, `avvisaTelegram`, builder messaggi | Si | Nessun canale blocca il flusso |
| `notifiche.gs` | `avvisaChat` | Invia webhook Google Chat | messaggio | HTTP request | `UrlFetchApp`, `CONFIG.WEBHOOK_CHAT` | Si | Markdown leggero |
| `notifiche.gs` | `avvisaTelegram` | Invia messaggio Telegram HTML | messaggio HTML | HTTP request | `UrlFetchApp`, `CONFIG.TELEGRAM_TOKEN` | Si | `parse_mode=HTML` |
| `notifiche.gs` | `_costruisciMessaggioChat` | Compose messaggio Chat pratica | dati pratica | stringa | nessuna esterna | Si | Testo leggibile |
| `notifiche.gs` | `_costruisciMessaggioTelegramHtml` | Compose messaggio Telegram pratica | dati pratica | stringa HTML | `_escapeTelegramHtml` | Si | Escape campi dinamici |
| `notifiche.gs` | `_getUrlForm` | Restituisce URL form da config | nessuno | URL o null | `CONFIG` | Si | Protegge placeholder |
| `notifiche.gs` | `_escapeTelegramHtml` | Escape minimale HTML Telegram | valore | stringa sicura | nessuna | Si | `<`, `>`, `&` |
| `notifiche.gs` | `avvisaTeamSemplice` | Notifica generica multi-canale | messaggio | effetti notifiche | `avvisaChat`, `avvisaTelegram` | Si | Wrapper compatto |
| `notifiche.gs` | `avvisaTraghettamentoTeam` | Notifica il trasporto nel Limbo | totale, dettagliMail | Chat + Telegram | builder traghettamento | Si | Usata da `caronteTraghetta` |
| `notifiche.gs` | `_costruisciTraghettamentoChat` | Compose riepilogo traghettamento Chat | totale, dettagliMail | stringa | `_getUrlForm` | Si | Include Limbo URL |
| `notifiche.gs` | `_costruisciTraghettamentoTelegram` | Compose riepilogo traghettamento Telegram | totale, dettagliMail | stringa HTML | `_escapeTelegramHtml`, `_getUrlForm` | Si | Include link cliccabili |
| `virgilio.html` | `google.script.run.getAnagraficaVirgilio` | Carica anagrafiche al bootstrap | nessuno | popola select e team | Apps Script UI | Si | Fallback se errore |
| `virgilio.html` | `_popolaClienti` | Riempie la select clienti | array clienti | DOM aggiornato | DOM | Si | Aggiunge anche "+ Nuovo cliente..." |
| `virgilio.html` | `_popolaTecnici` | Riempie i tecnici attivi | array team | DOM aggiornato | DOM | Si | Usa fallback se team vuoto |
| `virgilio.html` | `_usaFallbackAnagrafica` | Fallback clienti se il server non risponde | nessuno | select minima | DOM | Si | Solo "Nuovo cliente" |
| `virgilio.html` | `_usaFallbackTecnici` | Fallback team se il server non risponde | nessuno | checkbox hardcoded | DOM | Si | Tecnici locali di ripiego |
| `virgilio.html` | `_aggiornaSitiDatalist` | Aggiorna suggerimenti siti per cliente | cliente selezionato | datalist DOM | `window._anagrafica` | Si | Dipende dai dati anagrafici |
| `virgilio.html` | `slugify` | Normalizza stringhe in slug | stringa | slug | regex | Si | Attualmente utile solo come helper |
| `virgilio.html` | `getCliente` | Legge il cliente attuale | DOM | stringa | `clienteSelect`, `nuovoCliente` | Si | Restituisce il valore finale |
| `virgilio.html` | `getPratica` | Legge il tipo pratica selezionato | DOM | codice pratica | radio `name="pratica"` | Si | Ritorna `null` se non selezionato |
| `virgilio.html` | `getTecnici` | Legge i tecnici selezionati | DOM | array nomi | checkbox `.t-check` | Si | Multi-selezione |
| `virgilio.html` | `aggiorna` | Rigenera il riepilogo | nessuno | effetto UI | `buildRiepilogo` | Si | Wrapper leggero |
| `virgilio.html` | `onClienteChange` | Gestisce cliente nuovo/esistente | select cliente | UI aggiornata | DOM | Si | Mostra campo nuovo cliente |
| `virgilio.html` | `vai` | Navigazione wizard e validazioni | step target | cambio pannello | DOM | Si | 4 step |
| `virgilio.html` | `buildRiepilogo` | Compone anteprima pratica | valori form | riepilogo HTML | DOM | Si | Mostra percorso Drive atteso |
| `virgilio.html` | `escapeHtml` | Escape base per il rendering | valore | stringa sicura | nessuna | Si | Protegge il riepilogo |
| `virgilio.html` | `apri` | Submit verso Apps Script | dati form | success screen o alert | `google.script.run.apriPraticaDaVirgilio`, `aggiungiClienteSito` | Si | Non invia dati diretti a Drive dal browser |
| `virgilio.html` | `mostraSuccessoVirgilio` | Mostra esito positivo e link Drive | risposta server | schermata successo | DOM | Si | Bottone "Apri cartella Drive" |
| `virgilio.html` | `ricomincia` | Reset del wizard | nessuno | form pulito | DOM | Si | Nessuna persistenza locale |
| `test.gs` | `caronteTest` | Collaudo pre-deploy completo | nessuno | log diagnostico | `SpreadsheetApp`, `DriveApp`, `GmailApp`, `UrlFetchApp`, `doPost` | Si | Verifica canali e endpoint |
| `test.gs` | `caronteTestFinale` | Test orchestrato finale | nessuno | esecuzione sequenziale | `caronteTest`, `testVirgilioSenzaDeploy`, `testGmailDaTraghettare` | Si | Include sleep per rate limit |
| `test.gs` | `testGmailDaTraghettare` | Test flusso Gmail su etichetta | mail etichettata | log diagnostico | `GmailApp`, `caronteTraghetta` | Si | Richiede mail reale di prova |
| `caronte_bridge.gs` | `caronteRiceviComandoDryRun` | Validazione metadata-only del comando Caronte Locale | payload JSON | risposta dry-run | pure JS | Si | Nessun effetto persistente |
| `caronte_bridge.gs` | `testCaronteBridgeDryRun` | Test puro del bridge | payload di prova | log + assert | pure JS | Si | Blocca campi vietati |
| `drive_staging_verify.gs` | `caronteConfiguraCartellaStagingDriveTest` | Configura ID cartella test | folderId | Script Property scritta | `PropertiesService` | Si | Solo setup esplicito |
| `drive_staging_verify.gs` | `caronteVerificaStagingDriveDryRun` | Verifica read-only del Limbo su Drive Desktop | payload metadata-only | risposta cloud_visible | `DriveApp`, `PropertiesService` | Si | Legge file + manifest, non modifica nulla |
| `drive_staging_intake_test.gs` | `caronteSetupStagingDriveTestIntake` | Configura tab test intake | spreadsheetId, sheetName | tab e props pronte | `SpreadsheetApp`, `PropertiesService` | Si | Tab separato da `Bucoliche` reale |
| `drive_staging_intake_test.gs` | `caronteRegistraStagingDriveTest` | Registra presa in carico test | payload metadata-only | risposta standard | `DriveApp`, `SpreadsheetApp` | Si | Scrive solo nel tab test |

### 2.2 Inventario Google Sheet attesi

| Spreadsheet / tab | Colonne / schema | Ruolo | Tipo | Appartenenza |
|---|---|---|---|---|
| `bucoliche` | `timestamp`, `origine`, `cliente`, `sito`, `pratica`, `anno`, `tecnici`, `note`, `url_cartella`, `id_drive`, `mittente_dominio`, `oggetto_email`, `nome_file`, `estensione`, `dimensione_kb`, `stato`, `timestamp_archiviazione` | Registro operativo append-only e aggiornamento allegati archiviati | Tecnico + applicativo | Bucoliche |
| `Clienti_Siti` | `cliente`, `sito`, `attivo`, `data_inserimento` | Anagrafica cliente/sito usata dal form | Applicativo | Anagrafiche |
| `Team` | `nome`, `email`, `ruolo`, `attivo` | Rubrica tecnici e destinatari notifiche | Applicativo | Anagrafiche |
| `TipiPratica` | `codice`, `descrizione`, `attivo` | Vocabolario pratiche del form | Applicativo | Anagrafiche |
| `Bucoliche_Eventi` | 20 colonne: `event_id`, `created_at`, `exported_at`, `machine_id`, `account_alias`, `source_email`, `source_message_id`, `source_message_uid`, `attachment_id`, `fingerprint`, `sha256`, `event_type`, `local_state`, `global_state_suggestion`, `staged_filename`, `staged_path`, `manifest_path`, `result`, `conflict_type`, `notes` | Vista eventi del local connector v1.1 | Tecnico | Adapter locale, non v1.0 |
| `Bucoliche_Conflitti` | 12 colonne: `event_id`, `detected_at`, `exported_at`, `machine_id`, `account_alias`, `fingerprint`, `conflict_type`, `source_message_id`, `attachment_id`, `sha256`, `staged_filename`, `notes` | Vista conflitti del local connector v1.1 | Tecnico | Adapter locale, non v1.0 |
| `Bucoliche_Stato` | 14 colonne: `fingerprint`, `last_event_at`, `machine_id`, `account_alias`, `source_email`, `attachment_id`, `sha256`, `current_global_state`, `last_result`, `conflict_type`, `staged_filename`, `staged_path`, `manifest_path`, `notes` | Stato consolidato per fingerprint | Tecnico | Adapter locale, non v1.0 |
| `Staging_Local_Test` | `timestamp`, `connector_type`, `account_alias`, `source_message_id`, `source_message_uid`, `attachment_id`, `original_filename`, `staged_filename`, `sha256`, `size_bytes`, `mime_type`, `scan_engine`, `scan_result`, `quarantine_status`, `drive_file_found`, `manifest_found`, `manifest_consistent`, `drive_file_id`, `manifest_file_id`, `stato`, `note` | Tab test read-only / intake controllato | Tecnico | Test bridge locale |
| `Virgilio_Inbox` | `inbox_id`, `created_at`, `status`, `command_id`, `account_alias`, `source_email`, `source_message_id`, `source_message_uid`, `attachment_id`, `fingerprint`, `sha256`, `original_filename`, `staged_filename`, `drive_file_id`, `manifest_file_id`, `source_subject`, `source_sender`, `suggested_cliente`, `suggested_sito`, `suggested_pratica`, `form_url`, `notes` | Coda operativa dei documenti acquisiti da Caronte e in attesa di decisione umana/form Virgilio | Applicativo + tecnico di transizione | Virgilio Inbox |

Nota: `Virgilio_Inbox` deve restare separato sia da `bucoliche` v1.0 sia da `Bucoliche_Eventi` v1.1. Non è un registro storico, ma una coda di lavorazione. Una volta completata l’archiviazione finale, il record può passare a stato `archiviato`, mentre la storia tecnica resta in Bucoliche e la storia applicativa resta nel log Virgilio.

### 2.3 Inventario struttura Drive

| Elemento Drive | Regola / standard | Dove emerge | Riutilizzo |
|---|---|---|---|
| Limbo | Cartella staging dentro Empireo; contiene allegati traghettati prima della pratica | `caronte.gs`, `docs/archive/03_SICUREZZA_E_TEST.md` | Si |
| Empireo / `01_commesse_Sigma+` | Radice documentale del prototipo | `test.gs`, `caronte.gs`, `docs/archive/01_ARCHITETTURA_E_ROADMAP.md` | Si |
| Cliente | Sotto-cartella diretta dentro Empireo | `creaCartellaPratica` | Si |
| Sito | Sotto-cartella dentro cliente | `creaCartellaPratica` | Si |
| Pratica | Cartella `anno_pratica` allo stesso livello delle cartelle trasversali | `creaCartellaPratica` | Si |
| `00_autorizzazioni` | Cartella trasversale standard nel sito | `caronte.gs`, `virgilio.html`, `test.gs` | Si |
| `01_dati-ditta` | Cartella trasversale standard nel sito | `caronte.gs`, `virgilio.html`, `test.gs` | Si |
| `02_corrispondenza` | Cartella trasversale standard nel sito; qui finiscono gli allegati dal Limbo | `caronte.gs` | Si |
| Adamo | Template cartelle che viene copiato o usato come fallback | `caronte.gs`, `test.gs` | Si |
| Naming file nel Limbo v1.0 | `yyyy-MM-dd_dominio_messageid_nome_originale` sanitizzato | `caronte.gs::_salvaAllegatoInLimbo` | Si |
| Naming staging locale v1.1 | `attachment_id-sanitized_filename` + `.manifest.json` + temp `.uploading` / `.partial` | `local_connector/src/virgilio_connector/staging_transport.py` | No, e` solo per il ponte locale |

### 2.4 Inventario form HTML

| Campo / area | ID / origine | Cosa chiede | Chiamate | Esito al submit | Nota |
|---|---|---|---|---|---|
| Logo e nome | `virgilioIconDataUri` server-side | Branding del form | `_creaOutputVirgilio_` | Render HTML | Fallback `V` se il logo manca |
| Cliente | `clienteSelect` + `nuovoCliente` | Cliente esistente o nuovo | `getAnagraficaVirgilio`, `aggiungiClienteSito` | Valida prima del passaggio step | Nuovo cliente mostra campo dedicato |
| Sito | `sitoInput` | Sito / stabilimento | `datalist` popolato da anagrafiche | Valido se non vuoto | Usato nel riepilogo e nella cartella |
| Tipo pratica | `praticaGrid` | Codice pratica | `TIPI` JS e `getPratica()` | Obbligatorio | Es. AUA, AIA, VIA, EoW, TR |
| Anno | `annoSelect` | Anno apertura | JS generato dinamicamente | Obbligatorio | Range anno corrente +/- 3 |
| Tecnici | `tecniciWrap` | Team assegnato | `getAnagraficaVirgilio` | Array nomi | Multi-selezione |
| Note | `noteInput` | Note operative | nessuna | Testo libero | Passa a notifica e registrazione |
| Submit | `apri()` | Avvia apertura pratica | `google.script.run.apriPraticaDaVirgilio` | Success screen o alert | Disabilita il bottone durante l'operazione |
| Success screen | `mostraSuccessoVirgilio()` | Conferma creazione cartella | risposta server | Mostra link Drive | L'utente vede il percorso finale |

### 2.5 Flusso Virgilio 1.0

```text
mail / allegato
  -> Limbo Gmail / Drive
  -> trig. Caronte / polling
  -> salvataggio allegato nel Limbo Drive
  -> riga su Bucoliche
  -> notifica Chat/Telegram
  -> form Virgilio (HTML)
  -> dati utente + anagrafiche
  -> doPost / apriPraticaDaVirgilio
  -> creaCartellaPratica in Empireo
  -> avvisaTeam
  -> aggiorna Bucoliche / sposta allegati in 02_corrispondenza
  -> conferma finale all'utente
```

## 3. Cosa produce Caronte v1.1

La parte locale v1.1 produce un contratto piu` ricco e piu` rigido del vecchio Apps Script:

- comando metadata-only `local_imap_dry_run`;
- `schema_version`, `connector_type`, `requested_action`, `dry_run`;
- `command_id`, `account_alias`, `mailbox`, `mailbox_uidvalidity`, `message_uid`, `message_id`, `thread_id`;
- `attachments[]` con `local_temp_id`, `original_filename`, `sanitized_filename`, `mime_type`, `size_bytes`, `sha256`, `quarantine_status`, `scan_engine`, `scan_result`;
- staging filesystem con file `staged_filename` + `manifest_filename`;
- manifest JSON con `attachment_id`, `source_message_id`, `source_message_uid`, `account_alias`, `staged_at`, `note`, `dry_run`;
- stato locale SQLite con eventi, conflitti e stato consolidato per `fingerprint`;
- output Bucoliche v1.1 su `Bucoliche_Eventi`, `Bucoliche_Conflitti`, `Bucoliche_Stato`;
- opzionale tab di test `Staging_Local_Test`.

In pratica, Caronte v1.1 e` piu` forte sul lato tecnico, ma meno compatibile con il vecchio ingresso umano di Virgilio 1.0.

## 4. Gap principali

1. `Virgilio 1.0` chiede dati applicativi umani (`cliente`, `sito`, `pratica`, `anno`, `tecnici`, `note`), mentre `Caronte v1.1` produce soprattutto metadati tecnici di allegato.
2. `Caronte v1.1` usa `local_temp_id`, `sha256`, `fingerprint`, `staged_filename`, `staged_path`, `manifest_path`; il `doPost` storico di Virgilio non li consuma.
3. `Apps Script` non puo` leggere path locali del PC e non deve ricevere byte o base64.
4. Le tabelle non coincidono: `bucoliche` v1.0 e` append-only + update allegati, mentre v1.1 usa `Bucoliche_Eventi` / `Bucoliche_Stato` / `Bucoliche_Conflitti`.
5. `id_drive` in v1.0 e` un identificativo Google Drive finale; nello staging locale v1.1 non c'e` ancora un Drive file id affidabile.
6. I timestamp non sono omogenei: v1.0 usa timestamp locale stringa, v1.1 usa spesso ISO 8601 e aggregazioni per fingerprint.
7. Il matching tra allegato e pratica in v1.0 e` temporale e umano; in v1.1 e` per metadati e fingerprint.
8. `Staging_Local_Test` e` un tab di test, non una coda operativa da riusare senza distinguere il perimetro.

## 5. Ponte minimo consigliato

### Opzione preferita

Creare un ponte metadata-only molto piccolo sul lato Apps Script, con una sola idea: non trasportare byte, ma solo una riga di correlazione leggibile.

Schema:

1. Caronte Locale emette il suo comando dry-run / staging metadata-only.
2. Apps Script riceve un JSON minimale con `command_id`, `attachment_id` o `local_temp_id` correlabile, `sha256`, `staged_filename`, `source_message_uid`, `account_alias`, `note`, e gli esiti di validazione.
3. Il ponte scrive una riga in un tab inbox minimale nel foglio Bucoliche, idealmente `Virgilio_Inbox`; se il tab non esiste ancora, va creato come tab tecnico separato, non dentro `bucoliche`.
4. Il form Virgilio resta invariato e continua a fare la parte umana: scelta cliente/sito/pratica/anno, creazione cartella, notifica e archiviazione finale.

### Mapping stabile manifest locale -> `Virgilio_Inbox`

Il mapping minimo concordato e` questo:

| Colonna `Virgilio_Inbox` | Origine | Regola |
|---|---|---|
| `inbox_id` | non ancora valorizzato | verra` generato dal task schema/intake successivo |
| `created_at` | `manifest.created_at` fallback `manifest.staged_at` | primo timestamp disponibile del manifest |
| `status` | costante | `da_lavorare` |
| `command_id` | `manifest.command_id` | stringa vuota se il manifest locale non lo trasporta |
| `account_alias` | `manifest.account_alias` | copia diretta |
| `source_email` | `manifest.source_email` | copia diretta |
| `source_message_id` | `manifest.source_message_id` | copia diretta |
| `source_message_uid` | `manifest.source_message_uid` | copia diretta |
| `attachment_id` | `manifest.attachment_id` | copia diretta |
| `fingerprint` | `manifest.fingerprint` | chiave tecnica primaria per idempotenza futura |
| `sha256` | `manifest.sha256` | copia diretta |
| `original_filename` | `manifest.original_filename` | copia diretta |
| `staged_filename` | `manifest.staged_filename` | copia diretta |
| `drive_file_id` | lookup Drive successivo | non valorizzato dal manifest puro |
| `manifest_file_id` | lookup Drive successivo | non valorizzato dal manifest puro |
| `source_subject` | `manifest.subject` | copia diretta |
| `source_sender` | `manifest.source_sender` | copia diretta |
| `suggested_cliente` | non ancora valorizzato | resta vuoto fino a logica esplicita |
| `suggested_sito` | non ancora valorizzato | resta vuoto fino a logica esplicita |
| `suggested_pratica` | non ancora valorizzato | resta vuoto fino a logica esplicita |
| `form_url` | non ancora valorizzato | resta vuoto fino al task di apertura form |
| `notes` | `manifest.note`, `status_reason`, `source_mailbox`, `source_message_date`, `scan_result`, `policy_rule` | compattati come metadati leggibili, senza introdurre nuove colonne ora |

Conseguenze operative:

- il manifest locale e` gia sufficiente a costruire una preview stabile della riga inbox;
- i campi assenti dal manifest non vengono inventati;
- `drive_file_id`, `manifest_file_id`, `inbox_id` e `form_url` restano responsabilita` dei task successivi;
- `fingerprint` resta la chiave tecnica da usare per evitare duplicazioni future, senza riusare `Bucoliche_Stato` come inbox.

Perche` e` la scelta migliore:

- mantiene compatibilita` con Virgilio 1.0;
- richiede poco codice nuovo;
- non duplica la logica applicativa;
- usa Drive Desktop/Limbo condiviso solo come trasporto, non come nuova architettura;
- lascia il manifest leggibile da Apps Script;
- separa staging tecnico e decisione umana.

### Precisazione sul ruolo di `Virgilio_Inbox`

Il ponte Caronte → Virgilio non deve usare `Bucoliche_Eventi` o `Bucoliche_Stato` come inbox umana.

Questi tab possono essere usati come fonte tecnica per verificare che l’allegato sia stato acquisito, scansionato, esportato e non sia in conflitto, ma non devono diventare la lista operativa su cui lavora Ugo.

La lista operativa deve essere `Virgilio_Inbox`.

Regola:
- Caronte produce eventi e stato tecnico;
- il bridge crea o aggiorna un record in `Virgilio_Inbox`;
- il form Virgilio riceve un `inbox_id`;
- Ugo completa i dati mancanti;
- Virgilio archivia il file nella cartella finale;
- Bucoliche registra l’esito, ma non guida direttamente la decisione umana.

Questo evita di mescolare:
- audit tecnico;
- coda di lavorazione;
- dati applicativi;
- storico delle decisioni umane.

### Alternativa 1

Usare `Staging_Local_Test` come ponte temporaneo di import, con regole piu` stringenti e nessuna logica di produzione. Va bene solo se si vuole un passaggio intermedio quasi solo di prova.

### Alternativa 2

Nessun inbox tecnico: il team apre manualmente la pratica dal form Virgilio dopo aver letto il manifest. E` la soluzione piu` semplice ma porta meno automazione e piu` attrito operativo.

## 6. Roadmap per epiche

### Epica 0: Caronte locale chiuso

**Obiettivo**

Rendere definitivo il motore locale e bloccare il perimetro tecnico.

**Task**

- fissare il contratto metadata-only;
- tenere SQLite come registro primario;
- tenere i test di staging e bridge verdi;
- non toccare il form.

**File probabili**

- `local_connector/src/virgilio_connector/*.py`
- `docs/LOCAL_CARONTE.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`

**Rischi**

- drift tra manifest e tab;
- regressioni di contratto;
- confusione tra staging tecnico e archiviazione finale.

**Test di accettazione**

- dry-run metadata-only valido;
- nessun byte o path locale nel payload;
- nessuna scrittura Google non prevista.

**Cosa NON fare**

- non introdurre AI;
- non aggiungere GUI;
- non aprire il form nuovo.

### Epica 1: Ponte Caronte -> Virgilio 1.0

**Obiettivo**

Far arrivare a Google solo il minimo necessario per agganciare il flusso umano.
Virgilio 1.0 può prendere in carico solo file già visibili in Google Drive, non file presenti solo su disco locale.

**Task**

- definire il mapping tra manifest locale e inbox Apps Script;
- introdurre il tab inbox tecnico o equivalente;
- rendere leggibile il manifest dal lato Apps Script;
- evitare duplicazioni tra event sheet e form sheet.

**File probabili**

- `caronte_bridge.gs`
- `drive_staging_verify.gs`
- `drive_staging_intake_test.gs`
- eventuale nuovo `virgilio_inbox.gs`
- `bucoliche.gs`

**Rischi**

- collisioni di schema;
- id duplicati;
- confusione tra `attachment_id` e `sha256`.

**Test di accettazione**

- un solo comando produce una sola riga inbox;
- `sha256` e `attachment_id` restano coerenti;
- il payload non contiene byte o path locali.

**Cosa NON fare**

- non riscrivere il form;
- non sostituire Apps Script;
- non usare database remoti.

### Epica 2: Ripristino flusso umano / form / archiviazione finale / Chat / Telegram

**Obiettivo**

Riprendere il flusso completo lato umano senza rompere il motore esistente. 
Il form Virgilio 1.0 non viene riscritto. 
Può essere esteso solo per leggere un inbox_id e precompilare campi informativi già noti se pertinenti: nome file, mittente, oggetto, data, ecc...

**Task**

- lasciare il form com'e`, al massimo con prefill controllato;
- mantenere `anagrafiche.gs` come fonte dei dropdown;
- mantenere `creaCartellaPratica`;
- mantenere le notifiche Chat e Telegram;
- mantenere il refresh di Bucoliche.

**File probabili**

- `virgilio.html`
- `webapp.gs`
- `setup.gs`
- `anagrafiche.gs`
- `notifiche.gs`
- `caronte.gs`
- `bucoliche.gs`

**Rischi**

- notifiche duplicate;
- routing temporale errato dal Limbo;
- collisione tra pratiche simili.

**Test di accettazione**

- il form si apre;
- il submit crea la cartella corretta;
- l'utente vede il link finale;
- Chat e Telegram ricevono il messaggio giusto.

**Cosa NON fare**

- non cambiare la UX in modo invasivo;
- non introdurre routing complesso;
- non usare automazione irreversibile.

### Epica 3: UX decente e configurazione

**Obiettivo**

Rendere il sistema comprensibile e meno fragile all'uso quotidiano.

**Task**

- semplificare setup e diagnosi;
- mettere in ordine i messaggi di errore;
- documentare i canali e le props;
- rendere chiaro cosa e` test e cosa e` produzione.

**File probabili**

- `setup.gs`
- `docs/*.md`
- `virgilio.html`
- eventuali helper minimi di configurazione

**Rischi**

- drift documentale;
- eccesso di opzioni;
- manutenzione piu` lenta.

**Test di accettazione**

- setup leggibile;
- errori chiari;
- nessun segreto nei file versionati.

**Cosa NON fare**

- non creare un'altra GUI;
- non trasformare la documentazione in logica applicativa.

## 7. Test di accettazione

Per questo task documentale non serve una suite di test nuova.

Checklist di accettazione della documentazione:

- il documento esiste in `docs/VIRGILIO_V112_INTEGRATION_ROADMAP.md`;
- l'inventario cita i file reali presenti nel repo;
- il confronto distingue bene v1.0 Apps Script e v1.1 local connector;
- il ponte consigliato non richiede byte, path locali o riscrittura del form;
- le epiche dicono chiaramente cosa non fare.

Checklist di accettazione futura, quando si implementera` il ponte:

- dry-run bridge verde;
- staging verify read-only verde;
- intake test tab separato verde;
- nessuna chiamata reale non autorizzata;
- nessun segreto nel versioning.

## 8. Decisioni prese 

1. Ponte Caronte → Virgilio  
   Il ponte sarà temporaneo ma disciplinato.  
   Serve a integrare Caronte Locale con Virgilio 1.0 senza riscrivere subito la parte Google Apps Script. Dopo il primo periodo di uso reale verrà rivalutato se renderlo stabile o sostituirlo.

2. Tab operativo  
   Verrà creato un nuovo tab `Virgilio_Inbox`.  
   Non si userà `Staging_Local_Test` come tab operativo e non si userà `Bucoliche` come inbox.

3. Matching allegato-pratica  
   Il matching sarà umano nella prima fase.  
   Il sistema potrà proporre suggerimenti semplici, ma la decisione finale su cliente, sito, pratica e destinazione resterà all’utente. L’automazione potrà essere valutata solo dopo casi reali sufficienti.

4. Ruolo di Bucoliche  
   `Bucoliche` resta registro tecnico/storico, non inbox.  
   `Bucoliche_Eventi`, `Bucoliche_Stato` e `Bucoliche_Conflitti` servono per audit, stato e diagnostica. La coda operativa dei documenti da lavorare sarà `Virgilio_Inbox`.

5. Ruolo di `Staging_Local_Test`  
   `Staging_Local_Test` resta riferimento di contratto e ambiente di test.  
   Non diventa tab di produzione. Può essere usato per validare il formato dei dati, non per gestire il flusso operativo reale.
