# Virgilio

Virgilio e' un MVP interno per aiutare Sigma+ ad aprire pratiche, archiviare allegati e registrare le operazioni in modo piu' ordinato dentro l'ambiente Google Workspace.

La versione corrente usa Google Apps Script, Google Drive, Google Sheets, Gmail personale, Google Chat e Telegram. Il progetto e' funzionante come prototipo mono-utente, ma non e' ancora pronto per un deploy generalizzato a tutto il team.

## Stato attuale

**v1.0 - MVP Google Workspace mono-utente funzionante**

La v1.0 dimostra il flusso end-to-end su una singola casella Gmail e su un set controllato di cartelle e fogli Google. La prossima fase deve consolidare il prototipo, documentare i limiti e preparare l'evoluzione modulare senza trasformare Google Workspace in un vincolo definitivo.

## Obiettivo operativo

Virgilio riduce il costo operativo di apertura pratica e archiviazione documentale:

1. il tecnico compila un form o marca una email da lavorare;
2. il sistema crea o aggiorna la struttura Drive;
3. gli allegati utili vengono depositati nel Limbo;
4. le operazioni vengono registrate in Bucoliche;
5. il team riceve una notifica strutturata.

## Principio di sviluppo

**L'AI propone. Il tecnico valida. Il sistema registra.**

Questo principio vale anche per le evoluzioni future: nessuna automazione critica deve archiviare, inviare, classificare in modo definitivo o produrre effetti operativi senza revisione umana esplicita.

## Componenti attuali

| Componente | File | Ruolo |
|---|---|---|
| Virgilio HTML | `virgilio.html` | Interfaccia guidata per apertura pratica |
| Web App | `webapp.gs` | Pubblicazione e caricamento interfaccia |
| Caronte | `caronte.gs` | Creazione cartelle, Limbo, Gmail v1.0, Drive |
| Bucoliche | `bucoliche.gs` | Registro operativo su Google Sheets |
| Notifiche | `notifiche.gs` | Google Chat e Telegram |
| Anagrafiche | `anagrafiche.gs` | Clienti, siti, team, tipi pratica |
| Setup | `setup.gs` | Trigger, credenziali in PropertiesService |
| Test | `test.gs` | Test manuali del prototipo |

## Flusso attuale

```text
Tecnico
  -> Virgilio HTML oppure etichetta Gmail
  -> Apps Script
  -> Drive: Empireo / Limbo / cartelle pratica
  -> Sheets: Bucoliche
  -> Google Chat / Telegram
```

Per Gmail, la v1.0 usa `GmailApp` e quindi opera nel contesto della casella dell'utente esecutore. Il multi-mailbox non e' parte della v1.0.

## Limiti noti

- Il flusso Gmail e' mono-utente.
- Il Limbo e' una coda temporanea, non una quarantena completa.
- Bucoliche e' un registro operativo, non un database definitivo.
- Lo spostamento degli allegati richiede criteri piu' robusti prima di un uso condiviso.
- Le notifiche sono utili al prototipo, ma il canale definitivo e' da decidere.
- VTEnext, Cloud Run, Domain-Wide Delegation, Workspace Studio, Microsoft Graph e AI operativa sono opzioni future, non implementazioni correnti.
- Il progetto richiede una revisione di sicurezza prima del deploy condiviso.

## Test

I test Apps Script sono manuali e vanno eseguiti dall'editor Google Apps Script:

1. `caronteStatoCredenziali()`
2. `caronteTest()`
3. `testVirgilioSenzaDeploy()`
4. `testGmailDaTraghettare()` solo con una email di prova etichettata

Prima di eseguire test reali:

- usare dati fittizi o non riservati;
- non inserire token o webhook nel codice;
- verificare permessi Drive e Sheets;
- eliminare manualmente eventuali cartelle di test create nell'Empireo.

## Documentazione

- [Architettura e roadmap](docs/01_ARCHITETTURA_E_ROADMAP.md)
- [Decisioni e rischi](docs/02_DECISIONI_E_RISCHI.md)
- [Sicurezza e test](docs/03_SICUREZZA_E_TEST.md)
- [Ricognizione e connettori](docs/04_RICOGNIZIONE_E_CONNETTORI.md)
- [Workflow Git](docs/GIT_WORKFLOW.md)
- [Struttura repository](docs/REPO_STRUCTURE.md)

## Avvertenza

Virgilio e' un MVP interno. Non va considerato un prodotto pronto per l'uso generalizzato, ne' una piattaforma definitiva di gestione documentale, CRM o automazione AI.

Ogni estensione multi-utente deve passare da revisione condivisa, test progressivi, controllo sicurezza e decisioni esplicite su responsabilita', permessi, dati e manutenzione.
