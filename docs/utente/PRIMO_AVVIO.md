# Primo avvio di Caronte

Questa procedura prepara un nuovo utente all'uso ordinario di Virgilio. La
configurazione condivisa del Registro e del servizio di consegna deve essere
fornita dall'amministratore.

## Prima di iniziare

Occorrono:

- Caronte 1.1 installato sul computer Windows;
- Google Drive per desktop attivo e la cartella Limbo già sincronizzata;
- almeno una casella email accessibile;
- per Gmail o Google Workspace, un account autorizzato nel browser;
- per altra Posta IMAP, le informazioni di accesso fornite dal gestore della
  casella;
- un amministratore disponibile per completare Registro e consegna a Virgilio.

Non copiare password o codici in file del progetto. Inserirli soltanto nei
campi protetti di Caronte.

## 1. Benvenuto

Avvia Caronte e scegli **Inizia la configurazione**. Se compare direttamente
la Home, una configurazione esiste già: non sovrascriverla senza aver verificato
con chi gestisce Virgilio.

## 2. Scegli la cartella Limbo

1. Scegli **Scegli cartella...**.
2. Seleziona la cartella Limbo sincronizzata sul computer.
3. Scegli **Continua**.

Il percorso deve essere completo, esistente e corrispondere alla cartella
condivisa predisposta. Non creare una cartella omonima in un'altra posizione.

## 3. Configura almeno una casella

### Gmail o Google Workspace

1. Mantieni **Usa Gmail o Workspace**.
2. Inserisci un nome riconoscibile per la casella.
3. Inserisci l'indirizzo email.
4. Lascia selezionato **Casella attiva** se deve essere controllata.
5. Scegli **Collega con Google**.
6. Nel browser, seleziona l'account corretto e completa l'autorizzazione.
7. Attendi il messaggio di collegamento riuscito.

### Altra Posta IMAP

1. Scegli **Scegli Posta IMAP**.
2. Inserisci nome, indirizzo email e password della casella.
3. Controlla la cartella da acquisire, normalmente **da-traghettare**.
4. Se i valori proposti non corrispondono al servizio, apri **Mostra
   impostazioni avanzate** e usa i dati ricevuti dal gestore.
5. Scegli **Verifica e aggiungi** e attendi il risultato.

La verifica controlla che Caronte possa leggere la casella. Non avviarne una
seconda mentre compare **Collegamento e salvataggio in corso...**.

### Aggiungere o correggere altre caselle

La tabella mostra le caselle già predisposte. Seleziona una riga e usa
**Modifica** o **Rimuovi**. È possibile configurare più caselle, ma almeno una
deve essere presente. Una casella disattivata non partecipa ai controlli.

## 4. Controlla il riepilogo

Il riepilogo mostra:

- cartella Limbo;
- numero di caselle configurate e attive;
- nomi delle caselle.

Se un dato è errato, scegli **Indietro** e correggilo. Quando tutto è corretto,
scegli **Completa configurazione** per aprire la Home.

## 5. Completa Registro e consegna

Dalla Home apri **Registro e avvio**.

1. Controlla lo stato del **Registro delle attività**.
2. Se il Registro è configurato, scegli **Autorizza aggiornamento Registro** e
   nel browser usa un account autorizzato a modificare il foglio.
3. Controlla lo stato di **Consegna a Virgilio**.
4. Se uno dei due servizi non è pronto, scegli **Apri Caronte Manutenzione** e
   chiedi all'amministratore di completare la configurazione.

L'amministratore inserisce i dati condivisi una sola volta. L'utente non deve
indovinare o copiare da fonti non verificate l'indirizzo del Registro, quello
del servizio o la relativa chiave di accesso.

## 6. Scegli come avviare i controlli

Nella stessa schermata **Registro e avvio** puoi attivare il controllo
automatico all'accesso a Windows. In **Impostazioni** puoi inoltre scegliere:

- ogni quanti minuti controllare le caselle;
- se avviare Caronte all'accesso a Windows;
- se ridurlo a icona alla chiusura.

Per il primo collaudo è preferibile lasciare Caronte in pausa ed eseguire un
solo **Controlla ora** su un'email concordata.

## Verifica finale

La configurazione iniziale è pronta quando:

- la Home mostra almeno una casella attiva;
- il Limbo selezionato è quello sincronizzato;
- il Registro risulta configurato e autorizzato;
- la consegna a Virgilio risulta configurata;
- **Controlla ora** termina senza un problema persistente.

Se un controllo non riesce, non ripetere la configurazione da zero. Consulta
[Risoluzione problemi](RISOLUZIONE_PROBLEMI.md) e conserva il messaggio mostrato
in **Attività e problemi**.
