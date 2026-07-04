# GAS v1.1.3 evidence matrix - 2026-07-04

Decisione confermata: la base canonica da pushare e` `apps_script/src`.
Il mirror `apps_script/clasp` e` uno snapshot arretrato e il suo stato precedente e` stato archiviato in `apps_script/archive/pre_push_gas_20260704_114328/`.

Tentativo di snapshot live separato: `apps_script/archive/live_pull_pre_push_20260704_114803/`.
Esito: fallito con `invalid_grant / invalid_rapt`, quindi nessun pull live e` stato recuperato in questa sessione.

| Requisito v1.1.3 | Funzione/file atteso | Presente in `apps_script/src` | Presente in `apps_script/clasp` | Differenza rilevante | Decisione | Note |
|---|---|---|---|---|---|---|
| Canonico v1.1.3 completo | `webapp.gs`, `caronte.gs`, `virgilio.html`, `virgilio_inbox.gs` | Si | No | il set unificato vive in `src`, mentre il mirror non contiene il bridge inbox nuovo | `src` canonica | la scelta deriva dalle funzioni presenti, non dal nome della cartella |
| `Virgilio_Inbox` schema e setup | `caronteGetVirgilioInboxSchema()`, `caronteSetupVirgilioInbox()` | Si | No | il file `virgilio_inbox.gs` manca del tutto nel mirror | push da `src` | schema dedicato, header canonico e setup esplicito del tab |
| Record inbox e idempotenza | `caronteRegistraVirgilioInbox()`, `caronteRegistraVirgilioInboxDaGmail()`, `caronteGetVirgilioInboxForForm()`, `caronteCollegaSubmitVirgilioInbox()`, `caronteArchiviaVirgilioInbox()` | Si | No | lifecycle completo `da_lavorare -> in_lavorazione -> archiviato` solo in `src` | push da `src` | include generazione `inbox_id` e retry idempotente |
| Webapp e form | `doGet(e)`, `_caronteBuildVirgilioInboxTemplateContext_(e)`, `virgilio.html` | Si | Parziale | `clasp/webapp.js` usa ancora `doGet()` senza contesto inbox; il template puo` precompilare solo se il context viene iniettato | rigenerare `clasp` da `src` | `inbox_id` letto da query string e passato al template |
| Submit e archiviazione | `doPost(e)`, `apriPraticaDaVirgilio(dati)`, `_archiviaAllegatoVirgilioInbox_()`, `avvisaArchiviazioneVirgilioInbox()` | Si | Parziale | nel mirror il submit e` ancora legacy e non passa `inbox_id`; manca il ramo inbox-aware finale | `src` canonica | fallback legacy solo quando `inbox_id` non esiste |
| Limbo e pratica finale | `_trovaCartellaCorrispondenza()`, `_spostaAllegatiDalLimbo()`, `_archiviaAllegatoVirgilioInbox_()` | Si | Parziale | `_archiviaAllegatoVirgilioInbox_()` esiste solo in `src`; il resto e` vecchio e condiviso | push da `src` | il nuovo helper e` quello che collega il record inbox a `02_corrispondenza` |
| Registro e Bucoliche | `registraSuBucoliche()`, `registraErrore()`, `registraConflitto()` | Si | Si | la base audit e` presente in entrambi, ma `src` la integra nell'esito inbox-aware | mantenere e sincronizzare | audit leggibile e finale `archiviato` nel flusso corrente |
| Notifiche finali | `avvisaChat()`, `avvisaTelegram()`, `avvisaArchiviazioneVirgilioInbox()` | Si | Parziale | il mirror ha le notifiche generiche ma non la notifica dedicata all'archiviazione inbox | push da `src` | `avvisaArchiviazioneVirgilioInbox()` e` presente solo in `src` |
| Gmail-only ingress | `caronteTraghetta()`, `_processaMailUtente()`, `_salvaAllegatoInLimbo()` | Si | Si | il punto nuovo e` che `src` registra anche `Virgilio_Inbox` dopo il salvataggio nel Limbo | `src` canonica | il Gmail-only deve restare metadata-first e non riscrivere il form |
| Bridge local connector | `caronte_bridge.gs`, `caronteRiceviComandoDryRun()`, `caronteBuildVirgilioInboxDraftFromManifest()`, `caronteBuildVirgilioInboxDraftFromGmail()` | Si | Parziale | il mirror contiene solo il dry-run metadata-only; mancano i draft inbox completi | push da `src` | nessun byte, base64 o path locale verso Apps Script |
| Setup e diagnostica | `setup.gs`, `drive_staging_verify.gs`, `test.gs`, `anagrafiche.js`, `bucoliche.js`, `drive_staging_intake_test.js` | Si | Si | `setup.js` e `drive_staging_verify.js` differiscono ma non cambiano la decisione canonica | mantenere e riallineare | `anagrafiche`, `bucoliche`, `drive_staging_intake_test` e `test` risultano gia` allineati o compatibili |
| File solo nel mirror clasp | `drive_staging_bucoliche.js`, `drive_staging_gmail_label_move.js`, `drive_staging_notify.js`, `drive_staging_practice_move.js`, `p3_p4_preflight.js` | No | Si | sono file legacy P3/P4 e non fanno parte del flusso unificato v1.1.3 | archiviare ed escludere dal push | salvati nello snapshot pre-push; non vanno lasciati nel mirror da pubblicare |

Sintesi finale:

- `apps_script/src` contiene lo sviluppo v1.1.3 completo e coerente con il backlog chiuso.
- `apps_script/clasp` e` uno snapshot arretrato da rigenerare.
- i file legacy solo in `clasp` sono da considerare superati e gia` preservati nello snapshot archivio.
- la sync locale ha riallineato il mirror e il push finale e` stato completato dopo il refresh auth esterno al repository.
