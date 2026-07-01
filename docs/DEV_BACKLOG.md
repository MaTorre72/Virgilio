# Backlog di sviluppo

Stati: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`. Ordine operativo: priorita, poi ordine di tabella.

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
| V112-E1-T01 | TODO | P0 | Definire mapping manifest locale -> `Virgilio_Inbox` | Epica 0 chiusa | `caronte_bridge.gs`, `drive_staging_verify.gs`, `docs/*.md` | mapping documentato e stabile tra manifest e inbox | non riusare `Bucoliche_Eventi`/`Bucoliche_Stato` come inbox |
| V112-E1-T02 | TODO | P0 | Creare o consolidare lo schema `Virgilio_Inbox` | mapping definito | `virgilio_inbox.gs`, `docs/*.md` | schema con `inbox_id` e campi minimi concordati | non usare `Staging_Local_Test` come produzione |
| V112-E1-T03 | TODO | P0 | Implementare intake Apps Script metadata-only idempotente | schema inbox, mapping manifest | `caronte_bridge.gs`, `virgilio_inbox.gs` | stesso allegato genera una sola riga, payload senza byte/base64/path | non trasportare contenuti binari o percorsi locali |
| V112-E1-T04 | TODO | P1 | Verificare visibilita` Drive prima della presa in carico | intake metadata-only | `drive_staging_verify.gs`, `caronte_bridge.gs` | il file deve essere visibile in Google Drive prima di creare o aggiornare inbox | non aggirare la verifica con riferimenti locali |

### Epica 2 - Ripristino flusso umano / form / archiviazione finale / Chat / Telegram

Stato: TODO, dipendente da Epica 1.

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
| V112-E2-T01 | TODO | P0 | Estendere il form per leggere `inbox_id` | Epica 1 pronta | `virgilio.html`, `webapp.gs` | il form legge `inbox_id` senza riscriverlo | non riscrivere il form o cambiare la UX in modo invasivo |
| V112-E2-T02 | TODO | P0 | Collegare submit form a record `Virgilio_Inbox` | `inbox_id` leggibile | `virgilio.html`, `caronte.gs`, `bucoliche.gs` | submit agganciato al record inbox corretto | non usare il form per creare un inbox nuovo senza correlazione |
| V112-E2-T03 | TODO | P1 | Archiviare file dal Limbo Drive alla cartella pratica finale | submit collegato | `caronte.gs`, `setup.gs` | file copiato nella cartella finale corretta e record archiviato | non trasformare `Staging_Local_Test` in produzione |
| V112-E2-T04 | TODO | P1 | Aggiornare Bucoliche/log e notifiche Chat/Telegram | archiviazione finale | `bucoliche.gs`, `notifiche.gs` | esito registrato e notifica inviata | non introdurre automazioni irreversibili senza conferma umana |

### Epica 3 - UX decente e configurazione

Stato: TODO, dipendente da Epica 1 ed Epica 2.

Criteri di accettazione:
- un operatore tecnico capisce cosa e` pronto o bloccato;
- un utente normale non vede dettagli macchina inutili;
- ci sono pochi comandi base;
- la GUI o il form non espongono fingerprint, manifest o SQLite salvo diagnostica avanzata.

| ID | Stato | Pri | Titolo | Dipendenze | File probabili | Accettazione | Fuori scope specifico |
|---|---|---|---|---|---|---|---|
| V112-E3-T01 | TODO | P1 | Semplificare comandi e distinzione test/produzione | Epica 1-2 visibili | `setup.gs`, `README.md`, `docs/*.md` | pochi comandi base e differenza test/prod chiara | non creare nuove superfici operative complesse |
| V112-E3-T02 | TODO | P1 | Rendere leggibili errori, stati e configurazione | Epica 1-2 visibili | `setup.gs`, `docs/*.md` | errori e stato comprensibili, endpoint e props configurati | non esporre fingerprint, manifest o SQLite in UX normale |
| V112-E3-T03 | TODO | P2 | Documentare il flusso utente finale | Epica 2 chiusa | `docs/*.md` | flusso utente chiaro, breve e coerente con il backlog | non trasformare la documentazione in logica applicativa |

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
