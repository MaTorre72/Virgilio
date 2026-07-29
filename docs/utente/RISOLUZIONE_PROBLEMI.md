# Risoluzione dei problemi per l'utente

Questa guida propone soltanto interventi sicuri per l'utente ordinario. Backup,
reset, modifica dei collegamenti condivisi e interventi sul Registro spettano a
chi gestisce Virgilio tramite **Caronte Manutenzione**.

## Prima regola

Apri **Attività e problemi**, seleziona la riga interessata e leggi prima
l'**Azione consigliata**. Riprova **Controlla ora** al massimo una volta. Se lo
stesso problema ritorna, fermati e segnala il caso: più tentativi non rendono il
documento più sicuro e possono confondere la ricostruzione dell'attività.

## Problemi frequenti

### Nessuna email trovata

Controlla che:

1. l'email sia nella cartella configurata per quella casella, normalmente
   **da-traghettare**;
2. la casella risulti attiva nella Home;
3. l'email contenga davvero un allegato da acquisire;
4. **Ultimo controllo** si sia aggiornato.

Se l'email è già stata elaborata, può comparire come **Duplicato riconosciuto**
o non generare una nuova lavorazione. Non duplicarla.

### Caronte è già in esecuzione

Un controllo è ancora attivo. Attendi che termini e osserva **Prossima azione**.
Non avviare una seconda finestra, non cancellare file di blocco e non terminare
il processo dal sistema operativo salvo indicazione dell'amministratore.

### Caronte è in pausa

Scegli **Avvia** per riattivare il controllo periodico oppure **Controlla ora**
per una singola esecuzione. La pausa non cancella caselle o documenti.

### Nessuna casella attiva

Apri **Caselle** e verifica che almeno una riga abbia **Casella attiva**. Se la
casella manca, aggiungila con la procedura del [Primo avvio](PRIMO_AVVIO.md). Se
esiste ma non accetta più l'accesso, coinvolgi chi gestisce la casella.

### Accesso alla casella rifiutato

Per Gmail o Google Workspace ripeti **Collega con Google** scegliendo l'account
corretto. Per altra Posta IMAP controlla i dati forniti dal gestore. Non provare
password casuali e non inviare la password nella richiesta di assistenza.

### Documento in attesa della sincronizzazione del Limbo

Attendi che Google Drive per desktop completi la sincronizzazione e lascia il
file nella sua posizione. Caronte riprova automaticamente al controllo
successivo. Se l'attesa persiste:

1. verifica che Drive per desktop sia attivo;
2. controlla che in **Impostazioni** sia selezionata la cartella Limbo prevista;
3. segnala il problema all'amministratore senza spostare il file.

### Documento in attesa in Da archiviare

L'acquisizione è riuscita, ma manca la decisione umana. Apri **Da archiviare**,
controlla il documento e completa il form. Se non conosci la pratica corretta,
chiedi conferma al responsabile e lascia il documento nella coda.

### Invio a Da archiviare non riuscito

Esegui un solo nuovo **Controlla ora**. Se l'esito resta **Problema**, comunica
all'amministratore nome del documento, casella e ora. Non caricare manualmente
una copia nel Limbo o in Da archiviare.

### Registro non pronto o collegamento Google non disponibile

Apri **Registro e avvio**. Se il Registro è configurato ma non autorizzato, usa
**Autorizza aggiornamento Registro** con l'account corretto. Se risulta non
configurato, scegli **Apri Caronte Manutenzione** e chiedi all'amministratore di
completare la predisposizione.

### Consegna a Virgilio non configurata

È necessaria **Caronte Manutenzione**. L'amministratore deve verificare il
servizio di consegna e la relativa chiave protetta. L'utente ordinario non deve
incollare indirizzi o codici trovati altrove.

### La cartella Limbo non è valida

Usa **Scegli cartella...** e seleziona una cartella esistente. Se non sai quale
sia il Limbo corretto, fermati e chiedi all'amministratore: creare una nuova
cartella con lo stesso nome non risolve il collegamento.

### Documento duplicato

**Duplicato riconosciuto** è normalmente una protezione, non un errore.
Controlla se il documento è già presente in Da archiviare o nella pratica. Non
rinominarlo e non inoltrare di nuovo l'email.

### Documento archiviato nella pratica sbagliata

Non tentare di correggere il Registro o spostare il file dal Limbo. Avvisa
subito il responsabile dell'archiviazione e l'amministratore, indicando il
documento e la destinazione scelta. La correzione deve mantenere leggibile la
cronologia.

### Caronte non si apre o non può aprire Caronte Manutenzione

Prova una sola volta a chiudere e riaprire Caronte. Se il problema resta,
segnala all'amministratore la versione visibile in **Informazioni su Caronte** e
il testo del messaggio. Non reinstallare o cancellare cartelle dati senza un
backup verificato.

## Informazioni utili per l'assistenza

Raccogli:

- data e ora del controllo;
- nome della casella, senza credenziali;
- nome del documento, se non contiene dati che non possono essere comunicati;
- attività, esito e azione consigliata mostrati da Caronte;
- versione riportata in **Informazioni su Caronte**;
- indicazione se il problema si ripete dopo un solo nuovo controllo.

Solo se l'amministratore lo richiede, seleziona la riga e usa **Mostra dettagli
tecnici**. Caronte Manutenzione può creare un report diagnostico destinato
all'assistenza; il report non sostituisce il backup.

## Operazioni da non usare come tentativo di riparazione

- cancellare o rinominare file nel Limbo;
- modificare a mano il Registro;
- spostare l'email avanti e indietro tra le cartelle;
- avviare più controlli o più copie di Caronte;
- disattivare protezioni o scansioni;
- eseguire un reset;
- condividere password, token o codici di accesso.

Se serve un intervento amministrativo, consulta la procedura tecnica indicata
da chi gestisce Virgilio; l'uso ordinario può riprendere quando la Home non
mostra più il problema e un controllo concordato termina correttamente.
