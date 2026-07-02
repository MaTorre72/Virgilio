# Backlog di sviluppo

Stati: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`. Ordine operativo: priorita, poi ordine di tabella.

## Milestone 0.0 - Separazione workspace Apps Script

Obiettivo: evitare la convivenza in root di sorgente canonica e snapshot `clasp`, cosi il lavoro
autonomo puo leggere, modificare e sincronizzare il progetto senza ambiguita di rappresentazione.

### Task 0.0 - Separare sorgente e snapshot Apps Script

Obiettivo:
spostare la sorgente Apps Script e la snapshot `clasp` in due cartelle dedicate, mantenendo il repo
leggibile e impedendo che il pull o il lavoro locale sovrascrivano file canonici.

Task:

- definire due cartelle separate per sorgente canonica e snapshot `clasp`;
- aggiornare `clasp`/ignore in modo coerente con la nuova struttura;
- mantenere i file Apps Script esistenti senza perdita o riscrittura cieca;
- lasciare root libera da conflitti tra `.gs` e snapshot sincronizzata.

Accettazione:

- sorgente e snapshot non condividono piu la stessa cartella;
- `clasp pull` non sporca la root con file ambigui;
- nessun file canonico viene sovrascritto o perso.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P0 | Separare sorgente e snapshot Apps Script | `.clasp.json`, `.claspignore`, cartelle dedicate Apps Script | root pulita, sorgente e mirror distinti, nessuna perdita di codice | Alto |

## Milestone 0 - Delta MVP operativo minimo

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P0 | Comando esplicito `refresh-bucoliche-state` senza append eventi | `bucoliche.py`, CLI, README | dry-run con preview; run reale aggiorna solo `Bucoliche_Stato` | Medio |
| DONE | P0 | Comando esplicito `ack-completed-messages` come wrapper controllato | CLI, completion, README | dry-run separato; gate export/conflitti/stato | Alto |
| DONE | P1 | GUI minima locale `tkinter` sopra configurazione e comandi | nuovo layer GUI, README, test smoke mirato | nessuna logica duplicata; CLI invariata | Medio |

## Milestone 1 - Stabilizzazione pilota locale

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P0 | Refresh `Bucoliche_Stato` derivato dagli eventi | `bucoliche.py`, CLI, test | fake Sheet; idempotenza; Eventi immutato | Medio |
| DONE | P0 | `pilot-run-safe`: sequenza completa controllata | pipeline, CLI | dry-run senza effetti; stop su gate | Alto |
| DONE | P1 | Report pilota finale leggibile | pipeline, reports | fixture; JSON sicuro e sintesi umana | Basso |
| DONE | P1 | Idempotenza end-to-end | SQLite, Bucoliche, test | doppio run senza duplicati | Alto |
| DONE | P1 | Eliminare `example.invalid` da dati operativi | manifest/state | fixture realistica; nessun placeholder esportato | Medio |
| DONE | P1 | Gestire `attachment_id=None` | state/export | legacy fixture; skip `legacy_incomplete` | Medio |
| DONE | P1 | Verificare secondo export gia esportato | Bucoliche test | zero append al retry | Medio |

## Milestone 2 - Usabilita minima

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P1 | Comando unico `virgilio pilot` | CLI | help, dry-run, exit code | Medio |
| DONE | P1 | Output umano oltre JSON | CLI/report | snapshot essenziale | Basso |
| DONE | P1 | Configurazione guidata | config/CLI | nessun segreto; config valida | Medio |
| DONE | P1 | Diagnostica errori comuni | doctor | fixture errori noti | Basso |
| DONE | P2 | README "10 comandi essenziali" | README | comandi verificati | Basso |

## Milestone 3 - Multi-postazione

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P1 | Simulare due `machine_id` | test/audit | fixture isolate | Medio |
| DONE | P1 | Merge eventi da due export | Bucoliche | ordine deterministico | Alto |
| DONE | P1 | Stato consolidato cross-machine | Bucoliche_Stato | una riga/fingerprint | Alto |
| DONE | P1 | Conflitti cross-machine | conflict detector | collisioni rilevate | Alto |
| DONE | P2 | Policy manuale risoluzione conflitti | docs/state | nessuna risoluzione automatica | Medio |

## Milestone 4 - Parsing allegati

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P2 | Confronto Docling/Unstructured su fixture | spike isolato | report qualita; nessuna produzione | Medio |
| DONE | P2 | Estrazione testo e tabelle senza AI | parser | fixture PDF/DOCX/XLSX | Alto |
| DONE | P2 | Manifest arricchito | manifest | schema retrocompatibile | Medio |

## Milestone 5 - Classificazione assistita

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P3 | Gateway LiteLLM | adapter futuro | mock provider; budget | Alto |
| DONE | P3 | Proposta classificazione | classifier futuro | nessuna azione automatica | Alto |
| DONE | P3 | Human review | workflow futuro | conferma obbligatoria | Alto |
| DONE | P3 | Feedback loop | audit futuro | correzioni tracciate | Alto |

## Milestone v1.1.3 - Virgilio unificato

Obiettivo: consolidare Virgilio come un solo flusso operativo con due ingressi tecnici, lessico comune e sviluppo Apps Script tramite `clasp`.

### EPICA 0 - Conciliazione e lessico comune

Obiettivo:
eliminare ambiguita` tra `staging`/Limbo, Bucoliche tecniche, `Virgilio_Inbox` e Registro.

Task:

- creare documento architettura unificata;
- mappare termini legacy -> termini ufficiali;
- individuare file e funzioni da preservare;
- classificare moduli Google-only e local connector.

Accettazione:

- lessico unico approvato;
- nessun modulo perso;
- backlog aggiornato.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P0 | Creare documento architettura unificata | `docs/ARCHITETTURA_UNIFICATA.md`, `README.md`, `AGENTS.md` | documento breve, coerente e condiviso | Medio |
| TODO | P0 | Mappare termini legacy -> ufficiali | `docs/ARCHITETTURA_UNIFICATA.md`, `docs/DEV_BACKLOG.md` | lessico unico per UX e backlog | Medio |
| TODO | P1 | Individuare funzioni da preservare | codice Apps Script, local connector | inventario delle aree da non perdere | Alto |
| TODO | P1 | Classificare moduli Google-only e local connector | `README.md`, docs | separazione chiara dei due ingressi | Medio |

### EPICA 1 - Registro unico di audit

Obiettivo:
razionalizzare Bucoliche in un Registro unico.

Task:

- definire schema minimo Registro;
- mappare eventi local connector nel Registro;
- mappare eventi Google-only nel Registro;
- trattare errori e conflitti come eventi di Registro;
- mantenere eventuali tab tecnici solo come compatibilita` temporanea.

Accettazione:

- un documento Google-only produce eventi Registro;
- un documento local connector produce eventi Registro;
- nessun nuovo tab tecnico produttivo viene creato senza necessita`.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P0 | Definire schema Registro unico | `docs/ARCHITETTURA_UNIFICATA.md`, `docs/NEXT_CODEX_TASKS.md` | schema minimo approvato | Medio |
| TODO | P1 | Mappare eventi local connector nel Registro | codice local connector, docs | eventi tracciabili senza perdita | Alto |
| TODO | P1 | Mappare eventi Google-only nel Registro | Apps Script, docs | eventi coerenti con il flusso unico | Alto |
| TODO | P1 | Trattare errori e conflitti come eventi di Registro | docs, codice tecnico | errori ispezionabili e non silenziati | Alto |
| TODO | P2 | Mantenere i tab tecnici solo per compatibilita` | docs, eventuali script legacy | nessun nuovo tab produttivo separato | Medio |

### EPICA 2 - Da archiviare / Virgilio_Inbox

Obiettivo:
definire e usare una sola coda operativa umana.

Task:

- consolidare `Virgilio_Inbox` come tab tecnico;
- chiamarlo `Da archiviare` nella UX/documentazione;
- definire schema minimo;
- generare `inbox_id`;
- garantire idempotenza;
- generare `form_url`.

Accettazione:

- un file nel Limbo produce una sola riga `Da archiviare`;
- secondo passaggio non duplica;
- stato iniziale `da_archiviare`;
- form apribile con `inbox_id`.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P0 | Consolidare `Virgilio_Inbox` come coda tecnica | Apps Script, docs | struttura coerente e non ambigua | Alto |
| TODO | P0 | Esporre `Da archiviare` nella UX | `README.md`, docs | lessico utente uniforme | Medio |
| TODO | P0 | Definire schema minimo inbox | Apps Script, docs | campi minimi e idempotenza | Alto |
| TODO | P1 | Generare `inbox_id` e `form_url` | Apps Script | record apribile dal form | Alto |

### EPICA 3 - Adapter Google-only

Obiettivo:
portare `GmailApp` dentro il flusso unico.

Flusso:
`GmailApp -> Limbo -> Da archiviare -> Form -> Pratica finale -> Registro`

Task:

- preservare funzioni esistenti `GmailApp`;
- dopo salvataggio in Limbo creare record `Da archiviare`;
- scrivere evento Registro;
- non archiviare automaticamente senza form;
- non usare Bucoliche come coda.

Accettazione:

- mail `GmailApp` produce file in Limbo;
- produce riga `Da archiviare`;
- produce evento Registro;
- link form funziona.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P0 | Preservare il perimetro Google-only esistente | Apps Script | nessuna regressione del flusso attuale | Alto |
| TODO | P1 | Creare record `Da archiviare` dopo il Limbo | Apps Script, docs | idempotenza e tracciamento | Alto |
| TODO | P1 | Scrivere evento Registro dal percorso Google-only | Apps Script, docs | audit coerente | Alto |

### EPICA 4 - Adapter Local connector

Obiettivo:
portare `IMAP` locale dentro il flusso unico.

Flusso:
`IMAP -> Quarantena -> Scan -> Limbo -> Da archiviare -> Form -> Pratica finale -> Registro`

Task:

- preservare `IMAP`, quarantena, scan, SQLite e ack;
- copiare solo file clean nel Limbo;
- creare record `Da archiviare`;
- scrivere evento Registro;
- mantenere idempotenza;
- non mandare path locali ad Apps Script.

Accettazione:

- mail `IMAP` produce file clean nel Limbo;
- produce riga `Da archiviare`;
- produce evento Registro;
- secondo run non duplica.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P0 | Preservare il perimetro local connector esistente | `local_connector/` | niente regressioni locali | Alto |
| TODO | P1 | Copiare solo file clean nel Limbo | `local_connector/` | niente byte o path locali verso Apps Script | Alto |
| TODO | P1 | Creare record `Da archiviare` dal local connector | `local_connector/`, Apps Script | idempotenza su secondo run | Alto |
| TODO | P1 | Scrivere evento Registro dal percorso locale | `local_connector/`, docs | audit unico e coerente | Alto |

### EPICA 5 - Form unico

Obiettivo:
un solo form per apertura manuale e archiviazione da Limbo.

Task:

- form senza `inbox_id` resta legacy/manuale;
- form con `inbox_id` mostra contesto documento;
- prefill solo informativo;
- submit archivia file nella pratica;
- aggiorna `Da archiviare`;
- scrive Registro;
- invia notifica.

Accettazione:

- form funziona in entrambe le modalita`;
- file archiviato in `02_corrispondenza`;
- stato diventa `archiviato`;
- notifica inviata.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P0 | Mantenere il form unico con fallback legacy | Apps Script webapp, HTML | apertura manuale e via `inbox_id` | Alto |
| TODO | P1 | Collegare submit al record inbox corretto | Apps Script | correlazione stabile e idempotente | Alto |
| TODO | P1 | Aggiornare stato e notifica dopo archiviazione | Apps Script, docs | esito leggibile e tracciato | Medio |

### EPICA 6 - UX e configurazione

Obiettivo:
rendere comprensibili i due profili.

Task:

- documentare Profilo Google-only;
- documentare Profilo Local connector;
- creare comandi e verifiche semplici;
- distinguere test e produzione;
- nascondere dettagli macchina all'utente normale.

Accettazione:

- utente capisce quale profilo usa;
- configurazione verificabile;
- errori leggibili;
- nessuna esposizione inutile di manifest, fingerprint o SQLite.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| TODO | P1 | Documentare i due profili operativi | `README.md`, docs | chiarezza per utenti e tecnici | Medio |
| TODO | P1 | Creare comandi e verifiche semplici | `README.md`, `docs/CLASP_WORKFLOW.md` | setup e controllo lineari | Medio |
| TODO | P2 | Distinguere test e produzione | `README.md`, docs | nessuna ambiguita` operativa | Medio |
| TODO | P2 | Nascondere dettagli macchina nella UX normale | UI, docs | niente manifest/fingerprint/SQLite visibili | Medio |

## Milestone v1.1.2 - Integrazione Caronte Locale -> Virgilio 1.0

Questa milestone traduce la roadmap in backlog eseguibile per i cicli autonomi successivi. Caronte Locale v1.1 resta il motore tecnico locale; Virgilio 1.0 resta il livello umano/Google finale; il ponte resta metadata-only.

### Decisioni architetturali vincolanti

- Il ponte e` temporaneo ma disciplinato.
- `Virgilio_Inbox` e` il nuovo tab operativo.
- Il matching allegato-pratica e` umano nella prima fase.
- `Bucoliche_Eventi`, `Bucoliche_Stato` e `Bucoliche_Conflitti` sono registri tecnici, non inbox.
- `Staging_Local_Test` resta riferimento di contratto e test, non produzione.
- Virgilio 1.0 puo` prendere in carico solo file gia` visibili in Google Drive.
- Caronte non scarica direttamente in Drive prima della scansione: prima quarantena locale, poi scan, poi staging/Limbo condiviso.

### Fuori scope fino a chiusura v1.1.2

- AI.
- RAG.
- Docling.
- LiteLLM.
- parsing automatico documenti.
- classificazione automatica pratica.
- nuovo database remoto.
- server web.
- nuova GUI complessa.
- riscrittura completa del form.
- sostituzione Apps Script con Python.
- uso operativo di `Staging_Local_Test`.
- uso di Bucoliche come inbox.
- trasporto byte/base64 verso Apps Script.
- archiviazione finale senza conferma umana.

### Ordine operativo consigliato per Codex

1. Implementare `Virgilio_Inbox` schema + setup Apps Script.
2. Implementare intake metadata-only idempotente.
3. Collegare Caronte Locale al bridge metadata-only.
4. Generare `form_url` o `inbox_id` apribile dal form.
5. Estendere il form con prefill minimale da `inbox_id`.
6. Collegare submit form a record `Virgilio_Inbox`.
7. Archiviare file dal Limbo Drive alla cartella pratica.
8. Registrare esito e notificare Chat/Telegram.
9. Pulire UX, comandi e configurazione.

### Epica 0 - Caronte locale chiuso

Stato: READY_FOR_FREEZE.

Criteri di accettazione:
- pilot-run idempotente;
- ack prudente funzionante;
- file clean copiati solo dopo scan;
- nessun allargamento funzionale.

| ID | Stato | Pri | Titolo | Dipendenze | File probabili | Accettazione | Fuori scope specifico |
|---|---|---|---|---|---|---|---|
| V112-E0-T01 | DONE | P1 | Confermare contratto metadata-only | roadmap v1.1.2, bridge locale | `local_connector/src/virgilio_connector/*.py`, `docs/*.md` | payload solo metadati, nessun byte o path locale | non estendere il contratto con allegati binari |
| V112-E0-T02 | DONE | P2 | Documentare policy allegati ammessi | contratto metadata-only | `docs/*.md`, `local_connector/README.md` | allegati ammessi e limiti chiari, scan prima dello staging | non introdurre nuove categorie di file o parsing automatico |
| V112-E0-T03 | DONE | P2 | Mantenere SQLite e quarantena locale come perimetro chiuso | contratto metadata-only | `local_connector/src/virgilio_connector/*.py`, `docs/*.md` | SQLite resta registro primario locale; quarantena locale prima dello staging Drive | non spostare il registro primario su Google o su servizi remoti |
| V112-E0-T04 | DONE | P2 | Congelare il perimetro Caronte | gating v1.1 completo | `docs/*.md` | nessun allargamento funzionale, regressioni coperte da contratto | non aprire nuovi flussi utente o nuove GUI |

### Epica 1 - Ponte Caronte -> Virgilio 1.0

Stato: TODO.

Criteri di accettazione:
- un allegato gia` staged/Drive produce una sola riga `Virgilio_Inbox`;
- secondo invio non duplica;
- `Virgilio_Inbox` contiene un `inbox_id`;
- il payload non contiene byte, base64 o path locali;
- `Bucoliche_Eventi` e `Bucoliche_Stato` restano registri tecnici, non inbox.

| ID | Stato | Pri | Titolo | Dipendenze | File probabili | Accettazione | Fuori scope specifico |
|---|---|---|---|---|---|---|---|
| V112-E1-T01 | DONE | P0 | Definire mapping manifest locale -> `Virgilio_Inbox` | Epica 0 chiusa | `caronte_bridge.gs`, `drive_staging_verify.gs`, `docs/*.md` | mapping documentato e stabile tra manifest e inbox | non riusare `Bucoliche_Eventi`/`Bucoliche_Stato` come inbox |
| V112-E1-T02 | DONE | P0 | Creare o consolidare lo schema `Virgilio_Inbox` | mapping definito | `virgilio_inbox.gs`, `docs/*.md` | schema con `inbox_id` e campi minimi concordati | non usare `Staging_Local_Test` come produzione |
| V112-E1-T03 | DONE | P0 | Implementare intake Apps Script metadata-only idempotente | schema inbox, mapping manifest | `caronte_bridge.gs`, `virgilio_inbox.gs` | stesso allegato genera una sola riga, payload senza byte/base64/path | non trasportare contenuti binari o percorsi locali |
| V112-E1-T04 | DONE | P1 | Verificare visibilita` Drive prima della presa in carico | intake metadata-only | `drive_staging_verify.gs`, `caronte_bridge.gs`, `virgilio_inbox.gs` | il file deve essere visibile in Google Drive prima di creare o aggiornare inbox | non aggirare la verifica con riferimenti locali |

### Epica 2 - Ripristino flusso umano / form / archiviazione finale / Chat / Telegram

Stato: DONE, dipendente da Epica 1.

Criteri di accettazione:
- il form si apre da un record `Virgilio_Inbox`;
- l'utente sceglie cliente, sito, pratica e responsabile;
- il file viene copiato nella cartella finale corretta;
- il record `Virgilio_Inbox` passa ad archiviato;
- Bucoliche/log registra l'esito;
- Chat/Telegram ricevono messaggio;
- nessuna automazione irreversibile senza conferma umana.

| ID | Stato | Pri | Titolo | Dipendenze | File probabili | Accettazione | Fuori scope specifico |
|---|---|---|---|---|---|---|---|
| V112-E2-T01 | DONE | P0 | Estendere il form per leggere `inbox_id` | Epica 1 pronta | `virgilio.html`, `webapp.gs`, `virgilio_inbox.gs` | il form legge `inbox_id` senza riscriverlo | non riscrivere il form o cambiare la UX in modo invasivo |
| V112-E2-T02 | DONE | P0 | Collegare submit form a record `Virgilio_Inbox` | `inbox_id` leggibile | `virgilio.html`, `caronte.gs`, `bucoliche.gs` | submit agganciato al record inbox corretto | non usare il form per creare un inbox nuovo senza correlazione |
| V112-E2-T03 | DONE | P1 | Archiviare file dal Limbo Drive alla cartella pratica finale | submit collegato | `caronte.gs`, `virgilio_inbox.gs` | file copiato nella cartella finale corretta e record archiviato | non trasformare `Staging_Local_Test` in produzione |
| V112-E2-T04 | DONE | P1 | Aggiornare Bucoliche/log e notifiche Chat/Telegram | archiviazione finale | `bucoliche.gs`, `notifiche.gs` | esito registrato e notifica inviata | non introdurre automazioni irreversibili senza conferma umana |

### Epica 3 - UX decente e configurazione

Stato: TODO, dipendente da Epica 1 ed Epica 2.

Criteri di accettazione:
- un operatore tecnico capisce cosa e` pronto o bloccato;
- un utente normale non vede dettagli macchina inutili;
- ci sono pochi comandi base;
- la GUI o il form non espongono fingerprint, manifest o SQLite salvo diagnostica avanzata.

| ID | Stato | Pri | Titolo | Dipendenze | File probabili | Accettazione | Fuori scope specifico |
|---|---|---|---|---|---|---|---|
| V112-E3-T01 | DONE | P1 | Semplificare comandi e distinzione test/produzione | Epica 1-2 visibili | `setup.gs`, `README.md`, `docs/*.md` | pochi comandi base e differenza test/prod chiara | non creare nuove superfici operative complesse |
| V112-E3-T02 | DONE | P1 | Rendere leggibili errori, stati e configurazione | Epica 1-2 visibili | `setup.gs`, `docs/*.md` | errori e stato comprensibili, endpoint e props configurati | non esporre fingerprint, manifest o SQLite in UX normale |
| V112-E3-T03 | DONE | P2 | Documentare il flusso utente finale | Epica 2 chiusa | `docs/*.md` | flusso utente chiaro, breve e coerente con il backlog | non trasformare la documentazione in logica applicativa |

## Registro avanzamento

- 2026-06-30 - Aggiunto `refresh-bucoliche-state`: rigenera solo `Bucoliche_Stato` da eventi locali, con dry-run che mostra preview e senza append su `Bucoliche_Eventi`.
- 2026-06-29 - Report pipeline arricchito con `human_summary` leggibile e sicura; test report verdi.
- 2026-06-29 - `pilot-run-safe` aggiunto come wrapper dry-run con stop su gate; test CLI/sequenza verdi.
- 2026-06-29 - `Bucoliche_Stato` rigenerato dagli eventi durante export; test fake/idempotenza verdi.
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
