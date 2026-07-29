# Manuale utente di Virgilio 1.1

## Che cos'è Virgilio

Virgilio organizza il percorso dei documenti ricevuti per email. Un documento
non viene archiviato automaticamente nella prima cartella disponibile: viene
acquisito, controllato, portato nel **Limbo**, presentato in **Da archiviare** e
infine affidato alla decisione di una persona. Ogni passaggio rilevante viene
annotato nel **Registro**.

Questo percorso permette di sapere:

- da quale casella proviene un documento;
- se il documento è stato acquisito correttamente;
- se attende ancora una decisione;
- se è già stato archiviato nella pratica finale;
- quale azione è consigliata quando qualcosa non procede.

## I nomi da conoscere

| Nome | Significato per l'utente |
| --- | --- |
| **Virgilio** | il sistema complessivo che porta il documento dall'email alla pratica |
| **Caronte** | l'applicazione Windows usata per controllare le caselle e seguire le attività |
| **Limbo** | l'area di passaggio dei documenti acquisiti, prima dell'archiviazione definitiva |
| **Da archiviare** | la coda in cui una persona esamina il documento e sceglie dove archiviarlo |
| **Registro** | la cronologia condivisa delle attività e degli esiti |
| **Caronte Manutenzione** | l'applicazione riservata a configurazione tecnica, backup e diagnosi |

Il Limbo non è l'archivio definitivo. Un file presente nel Limbo può essere
ancora in attesa di sincronizzazione o della decisione umana. Non spostarlo e
non rinominarlo manualmente per accelerare il processo.

## Chi fa che cosa

### Utente operativo

L'utente operativo:

- prepara le email da acquisire;
- usa la Home di Caronte;
- controlla i messaggi in **Attività e problemi**;
- decide la destinazione del documento in **Da archiviare**;
- segnala all'amministratore un problema persistente.

### Responsabile dell'archiviazione

La persona che lavora in **Da archiviare** verifica il contenuto e sceglie i
dati richiesti dal form, per esempio cliente, sito, pratica e destinazione. La
conferma del form è una decisione umana: Caronte non la sostituisce.

### Amministratore di Virgilio

L'amministratore prepara i collegamenti condivisi, autorizza il Registro,
controlla backup e integrità e usa **Caronte Manutenzione**. L'utente ordinario
non deve eseguire reset o cambiare il collegamento a Virgilio.

Una stessa persona può ricoprire più ruoli, ma deve usare l'applicazione
corretta per l'attività che sta svolgendo.

## Il percorso completo di un documento

1. L'utente individua un'email con un allegato utile e la assegna alla cartella
   configurata, normalmente **da-traghettare**.
2. Caronte controlla le caselle attive quando si sceglie **Controlla ora** o
   quando è attivo il controllo periodico.
3. Il documento viene acquisito e verificato prima di raggiungere il Limbo.
4. Dopo la sincronizzazione, Virgilio rende il documento disponibile in
   **Da archiviare**.
5. Una persona esamina il documento e compila il form con la pratica corretta.
6. Virgilio archivia il file nella destinazione finale e aggiorna il Registro.
7. Quando previsto dalla configurazione della casella, l'email viene indicata
   come conclusa solo dopo la verifica dell'archiviazione finale.

Se uno dei passaggi non è ancora concluso, il documento resta in attesa e può
essere ripreso dal controllo successivo. Non occorre creare una seconda copia o
rimettere la stessa email nella coda.

## Le schermate di Caronte

### Prima configurazione

Al primo avvio Caronte mostra un percorso guidato. Richiede una cartella Limbo
e almeno una casella. Il riepilogo finale consente di tornare indietro e
correggere i dati prima di salvare. La procedura completa è descritta in
[Primo avvio](PRIMO_AVVIO.md).

### Home

La Home riassume:

- **Stato generale**: indica se Caronte è pronto, in esecuzione, in pausa o
  richiede attenzione;
- **Caselle attive**: quante caselle partecipano al controllo;
- **Ultimo controllo**: data e ora dell'ultima esecuzione terminata;
- **Prossima azione**: cosa deve fare l'utente;
- **Attività recenti** e **Problemi**: un riepilogo del lavoro più recente.

I comandi principali sono:

- **Controlla ora**: esegue un controllo immediato;
- **Avvia**: abilita il controllo periodico;
- **Pausa**: sospende il controllo periodico senza cancellare la configurazione.

Non premere più volte **Controlla ora**. Se un controllo è già in corso,
Caronte rifiuta il secondo avvio e mantiene valido quello esistente.

### Caselle

Da **Caselle** si possono aggiungere, modificare, attivare o disattivare le
caselle controllate. Per Gmail o Google Workspace si usa **Collega con
Google**. Per altri servizi si usa **Scegli Posta IMAP** e, se necessario,
**Mostra impostazioni avanzate**.

Una casella disattivata resta configurata ma non viene controllata. Prima di
rimuovere una casella, verificare che non contenga documenti ancora da
completare.

### Attività e problemi

Questa schermata mostra, per ogni evento leggibile:

- quando è avvenuto;
- quale casella e quale documento riguarda;
- l'attività svolta;
- l'esito;
- l'azione consigliata.

È possibile filtrare per casella, esito e data nel formato `gg/mm/aaaa`. I
dettagli tecnici sono utili solo quando l'amministratore li richiede; per l'uso
ordinario seguire prima l'azione consigliata.

### Impostazioni

Da **Impostazioni** si gestiscono:

- la cartella Limbo;
- l'intervallo tra i controlli periodici;
- l'avvio di Caronte all'accesso a Windows;
- la riduzione a icona quando si chiude la finestra.

La cartella Limbo deve essere quella già predisposta e sincronizzata. Cambiarla
senza coordinarsi con l'amministratore può lasciare documenti in attesa.

### Registro e avvio

La schermata **Registro e avvio** indica se:

- il Registro condiviso è configurato;
- il servizio di consegna a Virgilio è pronto;
- il controllo automatico all'accesso a Windows è attivo.

Quando il Registro è predisposto, l'utente autorizzato può scegliere
**Autorizza aggiornamento Registro** e selezionare nel browser l'account Google
che può modificare il foglio. Se il Registro o il servizio di consegna non sono
configurati, usare **Apri Caronte Manutenzione** e affidare l'operazione a chi
gestisce Virgilio.

## Significato degli esiti

| Esito | Che cosa significa | Che cosa fare |
| --- | --- | --- |
| **Riuscito** | il passaggio indicato è terminato | nessuna azione, salvo quella mostrata nella riga |
| **In corso** | Caronte sta ancora lavorando | attendere senza avviare un secondo controllo |
| **In attesa** | manca una sincronizzazione o una decisione umana | leggere l'azione consigliata e attendere o lavorare in Da archiviare |
| **Completato** | l'archiviazione finale è stata verificata | nessuna azione |
| **Ignorato** | l'elemento non richiedeva una nuova lavorazione, per esempio perché duplicato | non reinserire l'email |
| **Problema** | il passaggio non è terminato | riprovare una volta; se persiste, chiedere assistenza |

## Regole di sicurezza nell'uso quotidiano

- Inserire password e autorizzazioni solo nelle schermate previste.
- Non comunicare password, codici di accesso o collegamenti riservati via email,
  chat o segnalazione di assistenza.
- Non cancellare file dal Limbo, cartelle dati di Caronte o righe del Registro.
- Non rinominare i file per forzare un nuovo tentativo.
- Non eseguire un reset per risolvere un singolo documento bloccato.
- Non chiudere forzatamente Caronte durante un controllo, salvo indicazione
  dell'amministratore.
- Verificare sempre il contenuto e la pratica prima di confermare il form in
  Da archiviare.

## Quando il lavoro è davvero concluso

La presenza del file nel Limbo non basta. Il percorso è concluso quando il
documento risulta archiviato nella pratica corretta e l'attività mostra
**Completato** o **Pratica archiviata**. Se l'email di origine resta nella
cartella iniziale, non duplicarla: controllare prima l'esito in Caronte e la
configurazione prevista per quella casella.

Per la procedura passo passo continua con [Uso quotidiano](USO_QUOTIDIANO.md).
