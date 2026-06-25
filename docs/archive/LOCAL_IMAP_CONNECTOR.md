# Local IMAP Connector

## Scopo

Il Local IMAP Connector e' una possibile porta di ingresso locale per Virgilio. Gira sul PC dell'utente, osserva una sola cartella IMAP convenzionale e prepara gli allegati per Caronte senza sostituire il client email abituale.

LC3 include ora un adapter IMAP4/SSL read-only per una casella di test. Non
implementa scritture, ack o upload reali.

## Cosa fa

Il connettore, in una futura implementazione, potra':

1. leggere via IMAP una cartella esplicitamente configurata;
2. individuare messaggi selezionati intenzionalmente dall'utente;
3. scaricare gli allegati in una quarantena locale;
4. applicare filtri deterministici su nome, tipo e dimensione;
5. richiedere, se configurata, una scansione antivirus locale;
6. produrre un comando standardizzato verso Caronte;
7. attendere la conferma di Caronte;
8. eseguire l'ack della mail soltanto dopo un esito valido.

## Cosa non fa

- Non mostra inbox, conversazioni o anteprime email.
- Non invia, inoltra, risponde o compone email.
- Non sincronizza l'intera mailbox.
- Non indicizza il contenuto della posta.
- Non gestisce contatti, calendari o rubriche.
- Non archivia direttamente nel repository documentale definitivo.
- Non scrive direttamente in Bucoliche.
- Non invia notifiche Chat o Telegram.
- Non contiene AI.
- Non contiene credenziali nel codice o nei file versionati.

## Perche' non e' un client email

Il comando resta nel client scelto dall'utente: Gmail web, Outlook, Thunderbird, Apple Mail o altro. Il tecnico sposta o etichetta una mail nella cartella convenzionale; il connettore osserva solo quel perimetro ristretto e non offre funzioni di lettura o gestione quotidiana della posta.

## Cartelle convenzionali

| Cartella/label | Significato |
|---|---|
| `Virgilio/da-traghettare` | Comando esplicito dell'utente |
| `Virgilio/traghettate` | Ack completato dopo conferma di Caronte |
| `Virgilio/scartate` | Nessun allegato accettabile o rifiuto esplicito |
| `Virgilio/errore` | Errore tecnico che richiede verifica o nuovo tentativo |

La corrispondenza tra label Gmail e cartella IMAP dipende dal provider ed e' **DA VERIFICARE** durante il pilota.

## Flusso operativo

```text
Utente nel client email
  -> sposta/etichetta in Virgilio/da-traghettare
  -> Local IMAP Connector legge solo quella cartella
  -> download in quarantena locale non sincronizzata
  -> filtro deterministico
  -> eventuale scansione antivirus locale
  -> comando JSON standardizzato
  -> Caronte salva nel Limbo Drive e registra l'operazione
  -> risposta JSON di Caronte
  -> ack IMAP solo se almeno un allegato e' confermato
```

In caso di errore parziale, il connettore non deve dedurre il successo. L'ack deve dipendere dagli identificativi restituiti da Caronte, non dal solo codice HTTP.

## Relazione con Caronte

Caronte resta il nucleo operativo. Il connettore non conosce ID Drive, schema Bucoliche, webhook o logica delle pratiche. Invia un comando conforme a `docs/CONTRATTO_DATI_CARONTE.md` e interpreta una risposta standard.

Il trasporto del comando (HTTP, upload multipart o altra modalita') e' **DA DECIDERE**. Il contratto non implica che il futuro endpoint sia pubblico.

## Limbo locale

Il Limbo locale e' una quarantena tecnica sul PC dell'utente:

- contiene copie temporanee degli allegati;
- non deve essere sincronizzato con Drive, OneDrive o altri servizi;
- non deve aprire file automaticamente;
- conserva solo il tempo necessario al tentativo e alla gestione degli errori;
- usa identificativi locali opachi, non percorsi assoluti nel comando.

Le regole sono approfondite in `docs/QUARANTENA_LOCALE.md`.

## Limbo Drive

Il Limbo Drive resta sotto la responsabilita' di Apps Script. Un allegato passa allo stato `uploaded_to_limbo` solo quando Caronte restituisce l'identificativo Drive corrispondente. La presenza nella quarantena locale non equivale a salvataggio su Drive e non autorizza l'ack della mail.

## Limiti noti

- IMAP varia tra provider per cartelle, label, UID e modalita' di spostamento.
- Le credenziali locali richiederanno una strategia sicura non ancora definita.
- L'antivirus locale puo' non essere disponibile o aggiornato.
- Il PC puo' essere spento, offline o sospeso.
- Un file non segnalato dall'antivirus non e' garantito sicuro.
- La cancellazione e la retention locale richiedono regole verificabili.
- L'idempotenza tra retry, Caronte e ack deve essere progettata prima del codice reale.

## Decisioni aperte

| Tema | Opzioni | Stato |
|---|---|---|
| Libreria IMAP | `imaplib` standard library per il pilota read-only | SCELTA LC3 |
| Parsing email | `email` standard library, mail-parser | DA DECIDERE |
| Antivirus | ClamAV, Windows Defender, entrambi, nessuno obbligatorio | DA DECIDERE |
| Scanner assente | Fail closed, conferma manuale, prosecuzione con warning | DA DECIDERE |
| Formati iniziali | Solo PDF/immagini, anche Office senza macro | DA DECIDERE |
| Ack | Spostamento, copia, sola label/flag | DA DECIDERE |
| OAuth2 | Provider e modalita' futura | RINVIATA |
| Installazione | Comando manuale, script schedulato, servizio locale | DA DECIDERE |
| Trasporto a Caronte | JSON + upload separato, multipart, altro | DA DECIDERE |
| Retention locale | Cancellazione immediata, TTL breve, recupero manuale | DA DECIDERE |

## Roadmap a micro-fasi

### LC0 - Contratto e confini

- Documentazione architetturale.
- Contratto JSON di richiesta e risposta.
- Politica di quarantena proposta.
- Nessuna connessione reale.

### LC1 - Modello locale puro

- Modelli dati Python senza rete.
- Validazione payload.
- Sanitizzazione nomi e calcolo SHA-256 su file fittizi.
- Test automatici deterministici.

### LC2 - Quarantena locale

- Creazione directory fuori dalle cartelle sincronizzate.
- Stati e retention.
- Adapter antivirus simulato e testato.
- Nessun accesso IMAP.

Stato attuale: completata anche la simulazione offline del ciclo applicativo con
adapter in memoria. Il test end-to-end verifica che l'ack segua soltanto una
risposta Caronte coerente con hash e identificativo Limbo Drive.

### LC3 - Lettura IMAP in dry-run

- Un account di test.
- Una sola cartella convenzionale.
- Nessun ack e nessun upload.
- Log minimizzati.

Implementazione disponibile: `ImapReadonlyMailbox`. Usa `SELECT readonly=True`,
UID stabili nel contesto di UIDVALIDITY e `BODY.PEEK[]`. Le credenziali vengono
lette solo da variabili d'ambiente dal probe manuale e non sono persistite.

Il runner `ReadonlyQuarantineRunner` separa due modalita': dry-run senza scritture
locali e download controllato degli allegati ammessi. Il secondo registra run,
messaggi e allegati in `.local_data/state.db`; non importa ne' invoca Caronte.

### LC4 - Pilota end-to-end controllato

- Trasporto autenticato verso Caronte.
- Un solo utente e dati fittizi.
- Ack soltanto dopo conferma di almeno un allegato.
- Procedura di rollback documentata.
