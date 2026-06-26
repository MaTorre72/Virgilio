# Sicurezza e test

Questo documento raccoglie criteri di sicurezza e test per Virgilio/Caronte. Le voci sono prudenziali: indicano controlli da completare o verificare, non garanzie assolute.

## Principio

Il sistema deve essere:

- tracciabile;
- idempotente;
- reversibile;
- configurabile senza credenziali nel repository;
- capace di fermarsi in sicurezza su errore parziale.

## Sicurezza v1.0 Google Workspace

Prima di usare o estendere la v1.0:

- verificare permessi Drive;
- limitare accesso al Limbo;
- tenere token, webhook e segreti fuori dal codice;
- verificare utenti autorizzati alla Web App;
- documentare cosa viene loggato;
- verificare backup di Drive, Sheets e codice;
- separare test e produzione;
- mantenere possibilita' di rollback alla v1.0.

## Sicurezza Caronte Locale v1.1

Prima del pilota multi-casella:

- nessuna credenziale reale nel repository;
- `.env` escluso da Git;
- account IMAP configurati con `account_alias`;
- password/app password lette da variabili ambiente;
- log senza password, token o URL segreti;
- errore su una casella non deve bloccare le altre;
- stato separato per account;
- quarantena locale prima di ogni staging;
- scanner locale ove disponibile;
- nessuna apertura automatica degli allegati;
- nessun ack prima di presa in carico riuscita;
- idempotenza su `attachment_id` e `sha256`.

## Allegati malevoli

Il salvataggio su Drive o su una cartella sincronizzata non equivale a verifica di sicurezza. Un file puo' restare innocuo finche' non viene aperto, eseguito o sincronizzato in ambienti non controllati.

Contromisure minime per il pilota:

- allowlist iniziale di estensioni;
- blocco di eseguibili, script, macro e archivi rischiosi;
- quarantena locale;
- scanner locale;
- manifest JSON;
- hash SHA256;
- divieto di apertura automatica;
- staging separato dall'archivio definitivo;
- procedura manuale per file sospetti.

## Stati importanti

Gli stati devono essere espliciti. In particolare:

| Stato | Significato |
|---|---|
| `ready_for_scan` | Allegato scaricato ma non ancora verificato |
| `ready_for_caronte` | Allegato verificato localmente e pronto per fase successiva |
| `staged_local_drive` | Copia locale riuscita in cartella sincronizzata |
| `cloud_visible` | File/manifest visibili lato cloud |
| `presa_in_carico_test` | Registrazione test avvenuta |
| `registered_local` | Stato futuro: registrazione SQLite completata |
| `acked` | Stato futuro: mail chiusa sulla casella di origine |

`staged_local_drive` non significa `uploaded_to_drive`. `cloud_visible` non significa `archiviato`.

## Matrice test aggiornata

| ID | Area | Scenario | Output atteso | Stato |
|---|---|---|---|---|
| T01 | v1.0 | Apertura form Virgilio | Form caricato | Da verificare se serve |
| T02 | v1.0 | Creazione pratica | Cartella pratica creata | Da verificare se serve |
| T03 | v1.0 | GmailApp mono-utente | Thread elaborato solo nella casella esecutore | Limite confermato |
| T04 | IMAP | Lettura read-only | Nessuna modifica alla mail | Fatto |
| T05 | IMAP | `BODY.PEEK` | Nessun flag Seen involontario | Fatto |
| T06 | Quarantena | Download allegato | File locale + stato SQLite | Fatto |
| T07 | Scanner | File consentito | Stato `ready_for_caronte` | Fatto |
| T08 | Scanner | Scanner assente/errore | Stato prudenziale, non operativo | Fatto |
| T09 | Manifest | Generazione JSON | Manifest senza path locali/byte | Fatto |
| T10 | Dry-run | Invio metadata-only ad Apps Script | Nessun effetto operativo | Fatto |
| T11 | Drive Desktop | Staging locale | File + manifest copiati atomicamente | Fatto |
| T12 | Cloud verify | Verifica read-only | `cloud_visible=true` | Fatto |
| T13 | Intake test | Scrittura tab test | Una riga in `Staging_Local_Test` | Fatto |
| T14 | Idempotenza | Retry stesso allegato | Nessuna duplicazione | Da completare/verificare |
| T15 | Multi-account | Due caselle IMAP | Account separati, errore isolato | Da fare |
| T16 | Ack locale | Mail di origine | Spostamento/label sulla stessa casella IMAP | Da fare |
| T17 | SQLite primario | Registro locale | Stato completo senza Bucoliche | Da fare |
| T18 | Bucoliche adapter | Export opzionale | Nessun blocco se adapter fallisce | Da fare |
| T19 | Storage adapter | Cartella pratica | File assegnato correttamente | Da fare |
| T20 | Notifiche adapter | Notifica opzionale | Non blocca stato primario | Da fare |
| T21 | Pilota | Due utenti/caselle | Flusso completo con rollback | Da fare |
| T22 | AI | Classificazione | Fuori dal pilota v1.1 | Sospeso |

## Criteri pre-pilota v1.1

Prima del pilota con due utenti:

- multi-account IMAP locale configurato;
- almeno due caselle testate in read-only;
- quarantena separata o tracciata per account;
- ack IMAP locale testato su mail non critiche;
- SQLite locale come fonte primaria;
- Bucoliche solo come adapter opzionale;
- storage adapter scelto per il test;
- procedura rollback scritta;
- nessuna AI su dati reali;
- nessun segreto nel repository.

## Criteri di stop

Il sistema deve fermarsi senza procedere se:

- mancano credenziali/configurazione account;
- la cartella di staging non esiste;
- lo scanner segnala rischio o fallisce in modo ambiguo;
- hash post-copia non coincide;
- manifest non coerente;
- stato gia' registrato con hash diverso;
- ack richiesto prima del completamento dello stato locale;
- una casella non autorizzata viene trovata in configurazione.
