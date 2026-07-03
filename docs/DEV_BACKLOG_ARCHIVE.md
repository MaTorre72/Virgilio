# Archivio backlog

Questo file conserva lo storico chiuso e le milestone finite. Il backlog attivo resta in
`docs/DEV_BACKLOG.md`; il registro datato e` in `docs/CHANGELOG_DEV.md`.

## Milestone 0.0 - Separazione workspace Apps Script

Obiettivo: evitare la convivenza in root di sorgente canonica e snapshot `clasp`.

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P0 | Separare sorgente e snapshot Apps Script | `.clasp.json`, `.claspignore`, cartelle dedicate Apps Script | root pulita, sorgente e mirror distinti, nessuna perdita di codice | Alto |

## Milestone 0 - Delta MVP operativo minimo

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P0 | Comando `refresh-bucoliche-state` | `bucoliche.py`, CLI, README | dry-run con preview; run reale aggiorna solo `Bucoliche_Stato` | Medio |
| DONE | P0 | Wrapper `ack-completed-messages` | CLI, completion, README | dry-run separato; gate export/conflitti/stato | Alto |
| DONE | P1 | GUI minima locale `tkinter` | nuovo layer GUI, README, test smoke mirato | nessuna logica duplicata; CLI invariata | Medio |

## Milestone 1 - Stabilizzazione pilota locale

| Stato | Pri | Task e scopo | File probabili | Test / completamento | Rischio |
|---|---|---|---|---|---|
| DONE | P0 | Refresh `Bucoliche_Stato` dagli eventi | `bucoliche.py`, CLI, test | fake Sheet; idempotenza; Eventi immutato | Medio |
| DONE | P0 | `pilot-run-safe` | pipeline, CLI | dry-run senza effetti; stop su gate | Alto |
| DONE | P1 | Report pilota finale leggibile | pipeline, reports | fixture; JSON sicuro e sintesi umana | Basso |
| DONE | P1 | Idempotenza end-to-end | SQLite, Bucoliche, test | doppio run senza duplicati | Alto |
| DONE | P1 | Eliminare `example.invalid` | manifest/state | fixture realistica; nessun placeholder esportato | Medio |
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

## Milestone v1.1.3 - completamenti consolidati

I dettagli di avanzamento datati vivono in `docs/CHANGELOG_DEV.md`. Qui restano solo i task chiusi
spostati fuori dal backlog attivo.

- `V113-00-T01` - separazione sorgente/snapshot Apps Script.
- `V113-E0-T01` - mappa funzioni divergenti Google-only/local connector.
- `V113-E1-T01` - definizione schema Registro unico.
- `V113-E1-T02` - mappatura eventi local connector nel Registro.
- `V113-E1-T03` - trattamento errori e conflitti come eventi di Registro.
- `V113-E2-T01` - schema `Da archiviare`.
- `V113-E3-T01` - adapter Google-only verso `Da archiviare`.
- `V113-E3-T02` - completamento UX e configurazione, oggi archivio storico.

## Milestone v1.1.2 - Integrazione Caronte Locale -> Virgilio 1.0

Questa milestone e` storica e non va piu` caricata come contesto operativo fisso.

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

| ID | Stato | Pri | Titolo | Dipendenze | File probabili | Accettazione | Fuori scope specifico |
|---|---|---|---|---|---|---|---|
| V112-E0-T01 | DONE | P1 | Confermare contratto metadata-only | roadmap v1.1.2, bridge locale | `local_connector/src/virgilio_connector/*.py`, `docs/*.md` | payload solo metadati, nessun byte o path locale | non estendere il contratto con allegati binari |
| V112-E0-T02 | DONE | P2 | Documentare policy allegati ammessi | contratto metadata-only | `docs/*.md`, `local_connector/README.md` | allegati ammessi e limiti chiari, scan prima dello staging | non introdurre nuove categorie di file o parsing automatico |
| V112-E0-T03 | DONE | P2 | Mantenere SQLite e quarantena locale come perimetro chiuso | contratto metadata-only | `local_connector/src/virgilio_connector/*.py`, `docs/*.md` | SQLite resta registro primario locale; quarantena locale prima dello staging Drive | non spostare il registro primario su Google o su servizi remoti |
| V112-E0-T04 | DONE | P2 | Congelare il perimetro Caronte | gating v1.1 completo | `docs/*.md` | nessun allargamento funzionale, regressioni coperte da contratto | non aprire nuovi flussi utente o nuove GUI |

### Epica 1 - Ponte Caronte -> Virgilio 1.0

Stato: TODO.

| ID | Stato | Pri | Titolo | Dipendenze | File probabili | Accettazione | Fuori scope specifico |
|---|---|---|---|---|---|---|---|
| V112-E1-T01 | DONE | P0 | Definire mapping manifest locale -> `Virgilio_Inbox` | Epica 0 chiusa | `caronte_bridge.gs`, `drive_staging_verify.gs`, `docs/*.md` | mapping documentato e stabile tra manifest e inbox | non riusare `Bucoliche_Eventi`/`Bucoliche_Stato` come inbox |
| V112-E1-T02 | DONE | P0 | Creare o consolidare lo schema `Virgilio_Inbox` | mapping definito | `virgilio_inbox.gs`, `docs/*.md` | schema con `inbox_id` e campi minimi concordati | non usare `Staging_Local_Test` come produzione |
| V112-E1-T03 | DONE | P0 | Implementare intake Apps Script metadata-only idempotente | schema inbox, mapping manifest | `caronte_bridge.gs`, `virgilio_inbox.gs` | stesso allegato genera una sola riga, payload senza byte/base64/path | non trasportare contenuti binari o percorsi locali |
| V112-E1-T04 | DONE | P1 | Verificare visibilita` Drive prima della presa in carico | intake metadata-only | `drive_staging_verify.gs`, `caronte_bridge.gs`, `virgilio_inbox.gs` | il file deve essere visibile in Google Drive prima di creare o aggiornare inbox | non aggirare la verifica con riferimenti locali |

### Epica 2 - Ripristino flusso umano / form / archiviazione finale / Chat / Telegram

Stato: DONE, dipendente da Epica 1.

| ID | Stato | Pri | Titolo | Dipendenze | File probabili | Accettazione | Fuori scope specifico |
|---|---|---|---|---|---|---|---|
| V112-E2-T01 | DONE | P0 | Estendere il form per leggere `inbox_id` | Epica 1 pronta | `virgilio.html`, `webapp.gs`, `virgilio_inbox.gs` | il form legge `inbox_id` senza riscriverlo | non riscrivere il form o cambiare la UX in modo invasivo |
| V112-E2-T02 | DONE | P0 | Collegare submit form a record `Virgilio_Inbox` | `inbox_id` leggibile | `virgilio.html`, `caronte.gs`, `bucoliche.gs` | submit agganciato al record inbox corretto | non usare il form per creare un inbox nuovo senza correlazione |
| V112-E2-T03 | DONE | P1 | Archiviare file dal Limbo Drive alla cartella pratica finale | submit collegato | `caronte.gs`, `virgilio_inbox.gs` | file copiato nella cartella finale corretta e record archiviato | non trasformare `Staging_Local_Test` in produzione |
| V112-E2-T04 | DONE | P1 | Aggiornare Bucoliche/log e notifiche Chat/Telegram | archiviazione finale | `bucoliche.gs`, `notifiche.gs` | esito registrato e notifica inviata | non introdurre automazioni irreversibili senza conferma umana |

### Epica 3 - UX decente e configurazione

Stato: TODO, dipendente da Epica 1 ed Epica 2.

| ID | Stato | Pri | Titolo | Dipendenze | File probabili | Accettazione | Fuori scope specifico |
|---|---|---|---|---|---|---|---|
| V112-E3-T01 | DONE | P1 | Semplificare comandi e distinzione test/produzione | Epica 1-2 visibili | `setup.gs`, `README.md`, `docs/*.md` | pochi comandi base e differenza test/prod chiara | non creare nuove superfici operative complesse |
| V112-E3-T02 | DONE | P1 | Rendere leggibili errori, stati e configurazione | Epica 1-2 visibili | `setup.gs`, `docs/*.md` | errori e stato comprensibili, endpoint e props configurati | non esporre fingerprint, manifest o SQLite in UX normale |
| V112-E3-T03 | DONE | P2 | Documentare il flusso utente finale | Epica 2 chiusa | `docs/*.md` | flusso utente chiaro, breve e coerente con il backlog | non trasformare la documentazione in logica applicativa |
