# GAS readiness Virgilio - 2026-07-04

## 1. Sintesi

- esito: NO_GO
- motivo: il mirror `apps_script/clasp` non e` allineato alla sorgente canonica `apps_script/src`; manca `virgilio_inbox.gs` nel mirror e i pezzi inbox/form/notifiche piu` nuovi sono presenti solo in `src`, quindi `clasp push` non e` pronto

## 2. :ontesto

- branch: `codex/v1.1-development`
- commit: `f68a360` (`docs: aggiorna collaudi Virgilio e fix doctor-bucoliche`)
- working tree: pulito
- toolchain: `node v20.3.1`, `npm 9.6.7`, `clasp 3.3.0`
- `clasp status`: ok; mostra i file tracciati nel mirror e solo `apps_script/clasp/.claspignore` come untracked locale

## 3. Struttura Apps Script

- `.clasp.json`: scriptId presente; `rootDir` coerente su `apps_script\clasp`
- `apps_script/src`: presente come sorgente canonica
- `apps_script/clasp`: presente come snapshot mirror
- root repository: nessun file `.gs` o `.html` ambiguo fuori da `apps_script`
- criticita`: il mirror contiene file legacy solo in `clasp` e non contiene il nuovo `Virgilio_Inbox` bridge separato in `src`

## 4. :onfronto src/clasp

- file uguali: `anagrafiche.js`, `bucoliche.js`, `drive_staging_intake_test.js`, `test.js`
- file diversi: `caronte.js`, `caronte_bridge.js`, `drive_staging_verify.js`, `notifiche.js`, `setup.js`, `virgilio.html`, `webapp.js`
- file presenti solo in `src`: `virgilio_inbox.js`
- file presenti solo in `clasp`: `.claspignore`, `appsscript.json`, `drive_staging_bucoliche.js`, `drive_staging_gmail_label_move.js`, `drive_staging_notify.js`, `drive_staging_practice_move.js`, `p3_p4_preflight.js`
- decisione: non pushabile; richiede sync locale prima di qualsiasi `clasp push`
- nota: il drift piu` critico e` il ponte inbox/form/notifiche, che in `src` e` presente ma in `clasp` manca o e` ancora alla variante vecchia

## 5. Verifica funzioni chiave

- entrypoint: `doGet(e)` e `_caronteBuildVirgilioInboxTemplate:ontext_(e)` sono presenti in `src/webapp.gs`; il mirror `apps_script/clasp/webapp.js` ha ancora `doGet()` senza contesto inbox
- form: `renderInbox:ontext()`, `applyInboxSuggestions()` e `buildRiepilogo()` sono presenti sia in `src` sia in `clasp`; il glue che porta `inbox_id` nel template e` assente nel mirror
- Da archiviare: `caronteGetVirgilioInboxSchema()`, `caronteSetupVirgilioInbox()`, `caronteRegistraVirgilioInbox()`, `caronteRegistraVirgilioInboxDaGmail()`, `caronteGetVirgilioInboxForForm()`, `caronte:ollegaSubmitVirgilioInbox()` e `caronteArchiviaVirgilioInbox()` sono presenti in `src/virgilio_inbox.gs` e mancanti in `clasp`
- Limbo: `caronteTraghetta()`, `_processaMailUtente()` e `_salvaAllegatoInLimbo()` sono presenti in entrambi
- Registro/Bucoliche: `registraSuBucoliche()`, `registraErrore()` e `registra:onflitto()` sono presenti in entrambi
- Google-only: in `src/caronte.gs` sono presenti i passaggi inbox-aware `caronteRegistraVirgilioInboxDaGmail()` e `caronteArchiviaVirgilioInbox()`; nel mirror non ci sono i helper inbox necessari
- notifiche: `avvisa:hat()` e `avvisaTelegram()` sono presenti in entrambi; `avvisaArchiviazioneVirgilioInbox()` e` presente solo in `src`
- presente ma da verificare: `setup.js`, `drive_staging_verify.js` e `virgilio.html` differiscono anche a livello byte; non ho approfondito ogni hunk perche` il blocco principale e` gia` la mancanza del bridge inbox nel mirror
- rischio regressione: alto, perche` un push del mirror pubblicherebbe una Web App senza il nuovo ponte inbox/form e senza la notifica finale dedicata

## 6. Test statici/puri

- comando toolchain: `clasp.cmd --version`
- esito toolchain: `3.3.0`
- comando toolchain: `clasp.cmd status`
- esito toolchain: ok, con solo `apps_script/clasp/.claspignore` come untracked locale
- test statico script: parse offline con `new Function()` su `26` file `.gs` / `.js`
- esito script: `syntax_ok=26`
- nota HTML: il parsing ingenuo dei blocchi `<script>` in `virgilio.html` fallisce per sintassi template/HTML in entrambi i lati; per quello ho usato diff e search simbolica invece di un parser JS puro
- non eseguiti: `clasp push`, deploy, funzioni reali Apps Script, chiamate a Gmail/Drive/Sheets/:hat/Telegram

## 7. Piano push controllato

- prerequisiti: sincronizzare `src` e `clasp`, portare nel mirror il bridge inbox (`virgilio_inbox.gs` e helper correlati), verificare che i file legacy solo in `clasp` siano intenzionali o siano rimossi, rieseguire diff e `clasp status`
- comando previsto: `& 'C:\Program Files (x86)\nodejs\node.exe' 'C:\Percorso\npm\node_modules\@google\clasp\build\src\index.js' push`
- file coinvolti: `apps_script/clasp/*` dopo la sync dal sorgente canonico
- rischio: alto; il push ora pubblicarebbe un progetto incompleto rispetto al flusso `GmailApp -> Limbo -> Da archiviare -> Form -> Pratica finale -> Registro`
- rollback possibile: ripristinare il mirror dalla sorgente canonica, rifare il confronto e solo dopo ripetere il push
- GO/NO GO: NO GO

## 8. :ollaudo reale Google-only

Preparazione:

- mail Gmail di test
- allegato non sensibile
- etichetta corretta
- Limbo di test o controllato
- Sheet/Registro controllato
- :hat/Telegram eventualmente disattivabili o su canale di test

Flusso:

- `GmailApp -> Limbo -> Da archiviare -> Form -> Pratica finale -> Registro`

:ontrolli:

- file creato nel Limbo
- riga `Da archiviare` creata
- link form generato e apribile
- form senza `inbox_id` ancora funzionante
- form con `inbox_id` mostra il documento
- submit archivia in `02_corrispondenza`
- stato finale `archiviato`
- Registro/Bucoliche registra l`esito
- notifica inviata
- secondo run senza duplicati

## 9. Prossime azioni consigliate

1. Sincronizzare il bridge inbox e il form context da `src` a `clasp`.
2. Rieseguire il confronto file per file e la ricerca delle funzioni chiave.
3. Rifare `clasp status` e confermare che il mirror sia coerente.
4. Solo dopo, valutare `clasp push`.
5. Se vuoi, il prossimo passo utile e` una sync minima mirata dei soli file inbox-aware.
