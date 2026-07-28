# Virgilio 1.1

Virgilio acquisisce documenti dalle caselle configurate, li porta nel Limbo,
li espone in **Da archiviare**, raccoglie la decisione umana e li archivia nella
pratica finale registrando ogni transizione nel Registro.

La release ufficiale corrente e` **1.1.0**. Il percorso desktop e` stato
collaudato con esito umano `PASS` il 28 luglio 2026; la branch
`codex/v1.1-development` ne prepara la pubblicazione senza modificare `main`.

## Percorso utente

1. In **Caronte Manutenzione** si configurano caselle, collegamento a Virgilio,
   Limbo e preferenze operative.
2. In **Caronte** si avvia il controllo manuale oppure quello continuo.
3. Gli allegati ammessi passano dalla quarantena locale al Limbo Drive unico.
4. Virgilio crea una voce in **Da archiviare** e invia la notifica prevista.
5. L'utente apre il form, sceglie pratica e destinazione e conferma.
6. Il documento viene archiviato, il Registro riceve l'esito e solo allora la
   mail viene completata secondo la strategia configurata.

Riprese, retry e deduplicazione preservano lo stesso documento e non anticipano
il completamento della mail. `Virgilio_Inbox` e` il nome tecnico della coda
**Da archiviare**; `bucoliche` e` l'unico Registro cloud umano append-only.

## Componenti supportati

| Componente | Ruolo |
| --- | --- |
| `virgilio_connector.user_app` | applicazione utente **Caronte** |
| `virgilio_connector.maintenance_gui` | applicazione separata **Caronte Manutenzione** |
| `local_connector/src/virgilio_connector/` | servizi applicativi condivisi e connettore locale |
| `apps_script/src/` | adattatore Google canonico per form, coda, archivio e Registro |
| `local_connector/tests/` | test offline con fixture sintetiche |

Le implementazioni `gui` e `gui_*` sono legacy abbandonato: non sono superfici
supportate e non devono essere importate dalle nuove applicazioni.

## Prerequisiti operativi

- Windows 11 e un'installazione identificata di Caronte 1.1.0;
- Google Drive per desktop sincronizzato con il Limbo configurato;
- casella IMAP dedicata e credenziali salvate nel deposito protetto locale;
- client OAuth Desktop autorizzato quando la casella e` Google Workspace;
- collegamento al deployment Apps Script previsto e relativa chiave salvata
  localmente, mai nel repository;
- tab canonici `bucoliche`, `Virgilio_Inbox`, `Clienti_Siti`, `Team` e
  `TipiPratica` presenti e coerenti.

Configurazione, credenziali e dati locali non sono versionati. Test e sviluppo
non devono usare mail, account Google, credenziali o servizi reali.

## Limiti della 1.1.0

- la sincronizzazione del Limbo dipende da Google Drive per desktop e puo`
  richiedere retry limitati prima della presa in carico;
- Apps Script resta l'adattatore necessario al percorso Google pubblicato;
- il Registro cloud espone eventi umani; stato e conflitti tecnici restano
  locali;
- gli allegati macro-enabled, gli archivi compressi e gli eseguibili restano
  bloccati; i formati Office ammessi richiedono scansione;
- nessuna AI, RAG, Docling, LiteLLM, database remoto o server web fa parte della
  release;
- il completamento Gmail usa le estensioni IMAP del provider; per altri provider
  valgono le capacita` dichiarate dalla configurazione;
- reset, pubblicazioni Apps Script e operazioni reali richiedono procedure e
  autorizzazioni dedicate: non sono azioni ordinarie della GUI utente.

## Sviluppo e verifica

Il riferimento architetturale e` [Architettura unificata](docs/ARCHITETTURA_UNIFICATA.md).
Setup e test sono in [Setup e test](docs/SETUP_AND_TEST.md); il flusso locale e`
descritto in [Caronte Locale](docs/LOCAL_CARONTE.md). Il gate locale completo e`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1
```

La sorgente Apps Script canonica vive in `apps_script/src`; `clasp push` e deploy
non fanno parte delle verifiche locali e richiedono un task esplicito.

## Versioni e storia

`1.1.0` e` la release ufficiale. Gli installer `0.11.0-<commit>` citati nei
documenti di collaudo sono release candidate storiche e non sostituiscono la
release: la RC baseline `0.11.0-7e18277` conserva l'evidenza del `PASS` umano.
La storia pubblica e` in [CHANGELOG.md](CHANGELOG.md); le evidenze di sviluppo
restano nella documentazione interna fino al successivo consolidamento.

**L'AI propone. Il tecnico valida. Il sistema registra.**
