# Quarantena locale

## Staging e quarantena

Lo staging conserva temporaneamente un file in attesa del passaggio successivo. La quarantena aggiunge restrizioni operative: accesso limitato, nessuna apertura automatica, verifica del formato, eventuale scansione antivirus e stato esplicito prima dell'invio a Caronte.

Il Limbo locale del connettore deve essere trattato come quarantena, non come semplice cartella download.

## Posizione della cartella

La cartella deve:

- essere locale al PC;
- non trovarsi dentro Drive, OneDrive, Dropbox o cartelle sincronizzate;
- non essere una cartella aperta automaticamente dal file manager;
- avere permessi limitati all'utente e al processo del connettore;
- essere configurabile senza inserire il percorso nel repository;
- usare sottocartelle o identificativi non derivati direttamente da mittente e oggetto.

Il percorso predefinito per Windows, macOS e Linux e' **DA DECIDERE**. Prima dell'uso il connettore dovra' verificare, per quanto ragionevolmente possibile, che il percorso non sia sincronizzato.

## Nessuna apertura automatica

Il connettore non deve:

- aprire file o anteprime;
- invocare applicazioni associate;
- estrarre automaticamente archivi;
- eseguire macro, script o conversioni;
- montare immagini disco;
- rendere cliccabili i percorsi nei log operativi.

## Allowlist iniziale proposta

Proposta prudenziale per il primo prototipo, soggetta a conferma:

| Categoria | Estensioni | Note |
|---|---|---|
| PDF | `.pdf` | Verificare firma del file e MIME effettivo |
| Immagini raster | `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff` | Applicare limiti di dimensione |

Il supporto a documenti Office senza macro (`.docx`, `.xlsx`, `.pptx`) e' **DA DECIDERE**. La sola estensione non e' sufficiente: il controllo futuro dovra' confrontare nome, MIME dichiarato e firma del contenuto.

## Denylist iniziale proposta

Rifiutare almeno:

- eseguibili e librerie: `.exe`, `.com`, `.dll`, `.msi`, `.scr`;
- script: `.bat`, `.cmd`, `.ps1`, `.vbs`, `.js`, `.jse`, `.wsf`, `.sh`;
- collegamenti e contenuti attivi: `.lnk`, `.url`, `.hta`, `.chm`;
- immagini disco e pacchetti: `.iso`, `.img`, `.dmg`, `.pkg`;
- documenti Office con macro: `.docm`, `.xlsm`, `.pptm`;
- archivi: `.zip`, `.rar`, `.7z`, `.tar`, `.gz` nella prima fase;
- allegati crittografici non documentali: `.p7s`, `.smime` salvo requisito futuro.

La denylist riduce il rischio ma non rende sicuro un file ammesso.

## Antivirus locale

### ClamAV

Opzioni future:

- `clamscan`: processo per singola scansione, semplice ma potenzialmente lento;
- `clamd`: daemon persistente, piu' efficiente ma con installazione e configurazione aggiuntive.

Il connettore dovra' acquisire codice di uscita, versione motore e risultato senza includere contenuto del file nei log.

### Windows Defender

Su Windows si puo' valutare l'uso degli strumenti messi a disposizione da Microsoft Defender, se presenti e consentiti dalle policy aziendali. Percorso del comando, disponibilita' e codici di uscita devono essere rilevati, non hardcoded.

L'invocazione di Defender non e' implementata in questa fase.

### Scanner non configurato

Comportamento prudenziale proposto: stato `scan_failed` e nessun passaggio automatico a `ready_for_caronte`. Le alternative sono conferma manuale esplicita o prosecuzione con warning. La decisione definitiva e' **DA DECIDERE**.

## Stati allegato

| Stato | Significato | Passaggio successivo ammesso |
|---|---|---|
| `downloaded` | Byte ricevuti e scritti localmente | Verifica integrita' e filtri |
| `quarantined` | File isolato e in attesa di controllo | Scansione o revisione |
| `rejected` | File non ammesso da policy | Nessun upload |
| `scan_failed` | Scanner assente, errore o esito non interpretabile | Revisione o nuovo tentativo |
| `ready_for_caronte` | Filtri superati e policy scansione soddisfatta | Comando verso Caronte |
| `uploaded_to_limbo` | Caronte ha confermato il file nel Limbo Drive | Ack e pulizia secondo retention |

Transizioni proposte:

```text
downloaded -> quarantined
quarantined -> rejected
quarantined -> scan_failed
quarantined -> ready_for_caronte
ready_for_caronte -> uploaded_to_limbo
```

Non e' ammesso impostare `uploaded_to_limbo` sulla sola base di un tentativo HTTP o di un upload iniziato.

## Log minimi

Registrare soltanto:

- timestamp con timezone;
- livello e codice evento;
- `connector_id` e `command_id`;
- alias account, evitando credenziali;
- mailbox convenzionale;
- `message_uid` nel suo contesto;
- `local_temp_id`;
- nome sanitizzato, dimensione e SHA-256;
- transizione di stato;
- motore e risultato scansione;
- esito Caronte e possibilita' di retry.

Non registrare:

- password, token o stringhe di connessione;
- corpo email;
- contenuto allegati;
- percorsi locali completi se non indispensabili;
- indirizzi completi e oggetti nei log tecnici, salvo decisione motivata.

## Retention e pulizia

La retention e' **DA DECIDERE**. La futura implementazione dovra' distinguere:

- file caricati con successo, eliminabili dopo conferma e finestra breve;
- file rifiutati, eliminabili o isolabili secondo policy;
- errori retryable, conservabili per un TTL limitato;
- errori non retryable, da presentare all'utente senza conservazione indefinita.

La pulizia deve essere verificabile e non deve cancellare file fuori dalla radice di quarantena configurata.

## Responsabilita' dell'utente

L'utente deve:

- usare la cartella `Virgilio/da-traghettare` come comando intenzionale;
- non aprire manualmente file nella quarantena;
- mantenere sistema operativo e antivirus aggiornati;
- segnalare errori persistenti;
- verificare gli allegati scartati o in errore tramite la procedura concordata;
- non spostare la quarantena dentro cartelle sincronizzate;
- non condividere log o file di quarantena senza autorizzazione.

Il connettore riduce attivita' manuali ma non sostituisce le policy aziendali di sicurezza.
