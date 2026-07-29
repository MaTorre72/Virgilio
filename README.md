# Virgilio 1.1

![Icona Virgilio 1.1](icone/Virgilio_1.1.png)

Virgilio organizza il percorso dei documenti ricevuti via email: li acquisisce
in modo controllato, li porta nel **Limbo**, li presenta in **Da archiviare**,
raccoglie la scelta della pratica e registra l'esito nel **Registro**.

La versione ufficiale corrente e` **1.1.0**. La versione 1.0 e` storica e resta
recuperabile dal tag `v1.0`.

## Download e installazione

La distribuzione ufficiale e` nella
[Release Virgilio 1.1.0](https://github.com/MaTorre72/Virgilio/releases/tag/v1.1.0).
Per installare Caronte su Windows 11 x64 scaricare
[`CaronteSetup-1.1.0-68f3b90-build-20260729.exe`](https://github.com/MaTorre72/Virgilio/releases/download/v1.1.0/CaronteSetup-1.1.0-68f3b90-build-20260729.exe),
non gli archivi automatici **Source code**. L'installer e` per utente e include
Python e le dipendenze necessarie: Python non deve essere installato sul PC
dell'utente.

SHA-256 dell'installer:

```text
A6C87E6748ACC8C72970353B4686F219B28412D444847E7E436C818FB07DDB11
```

Il valore si controlla prima dell'avvio con:

```powershell
Get-FileHash .\CaronteSetup-1.1.0-68f3b90-build-20260729.exe -Algorithm SHA256
```

Il [manifest pubblicato](https://github.com/MaTorre72/Virgilio/releases/download/v1.1.0/CaronteSetup-1.1.0-68f3b90-build-20260729.manifest.json)
identifica versione, commit, build e smoke. La distribuzione pubblica non
incorpora client OAuth: per Gmail Workspace e Registro Google l'amministratore
predispone un proprio client Desktop esterno come descritto nella
[configurazione tecnica](docs/tecnica/CONFIGURAZIONE_E_INTEGRAZIONI.md).

## Cosa risolve

Senza Virgilio, allegati, cartelle Drive e decisioni sulla pratica possono
restare separati e difficili da ricostruire. Virgilio mantiene un unico flusso:

```text
Email
  -> acquisizione Google-only oppure IMAP locale
  -> quarantena e controllo, quando si usa Caronte Locale
  -> Limbo Drive
  -> Da archiviare
  -> decisione umana nel form
  -> pratica finale
  -> Registro
  -> completamento della mail di origine
```

Il documento e` l'unita` di lavoro. Una mail con piu` allegati e` conclusa solo
quando tutti i documenti ammessi hanno raggiunto la pratica finale.

## Applicazioni e componenti

| Nome | A chi serve | Responsabilita` |
| --- | --- | --- |
| **Caronte** | utente | controllare le caselle e seguire le attivita` |
| **Caronte Manutenzione** | amministratore | configurare, diagnosticare, fare backup e reset controllati |
| **Caronte Locale** | sistema | IMAP multi-account, quarantena, scan, stato e consegna |
| **Virgilio / form** | utente | scegliere cliente, sito, pratica e destinazione |
| **Apps Script** | integrazione | Drive, Da archiviare, form, Registro e notifiche Google |

La CLI e` una superficie per sviluppo e automazione. Usa gli stessi servizi
applicativi delle GUI e non rappresenta una terza applicazione utente.

## Due ingressi, un solo flusso

- **Google-only:** GmailApp acquisisce dalla casella dell'esecutore.
- **Local connector:** Caronte Locale legge una o piu` caselle IMAP, isola e
  scansiona gli allegati e completa la mail sulla casella di origine.

Entrambi usano lo stesso Limbo, la stessa coda Da archiviare, lo stesso form e
lo stesso Registro. SQLite conserva soltanto lo stato tecnico locale; non
sostituisce il Registro umano.

## Documentazione

L'[indice completo](docs/README.md) separa tre percorsi.

- [Manuale utente](docs/utente/README.md): primo avvio, lavoro quotidiano e
  problemi comuni.
- [Documentazione tecnica](docs/tecnica/README.md): architettura, dati,
  configurazione, comandi, sicurezza e manutenzione.
- [Documentazione per lo sviluppo](docs/sviluppo/README.md): roadmap,
  decisioni, workflow, backlog ed evidenze Codex.

Per orientarsi tecnicamente, iniziare da
[Architettura](docs/tecnica/ARCHITETTURA.md) e
[Modello dati e stati](docs/tecnica/MODELLO_DATI_E_STATI.md).

## Prerequisiti essenziali

- Per l'uso: Windows 11 x64, Google Drive per desktop per il Limbo, una casella
  IMAP e il deployment Apps Script dell'ambiente operativo.
- Per Gmail Workspace o Registro Google: client OAuth Desktop predisposto
  dall'amministratore fuori dal repository e dall'installer pubblico.
- Solo per lo sviluppo dal codice sorgente: Git e Python 3.11 o successivo.

Per l'utente la procedura completa e` in
[Primo avvio](docs/utente/PRIMO_AVVIO.md); clone, test e build sono descritti
separatamente in [Installazione e comandi](docs/tecnica/INSTALLAZIONE_E_COMANDI.md).

## Confini di sicurezza

- nessuna credenziale, token o configurazione reale e` versionata;
- gli allegati locali passano da quarantena, policy e scansione;
- Apps Script riceve metadati e ID, mai byte, base64 o percorsi locali;
- test e smoke usano soltanto fixture sintetiche e servizi simulati;
- ack, reset e deploy richiedono post-condizioni o autorizzazioni esplicite;
- AI, RAG, database remoti e server web non fanno parte della 1.1.

## Stato della release

La baseline collaudata e` il commit `7e18277`; il collaudo umano ha dato `PASS`
il 28 luglio 2026 e il deployment Apps Script associato e` `40`. Build,
installer e suite offline della 1.1.0 sono stati verificati prima della
pubblicazione. La build distribuita e` identificata dal commit `68f3b90`, dal
Build ID `254daca5-af1d-4951-85dd-f1119a3f0437` e dalla
[Release ufficiale](https://github.com/MaTorre72/Virgilio/releases/tag/v1.1.0).

Licenza: proprietaria, come dichiarato nel package locale.
