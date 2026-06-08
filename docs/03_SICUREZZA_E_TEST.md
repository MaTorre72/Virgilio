# Sicurezza e test

Questo documento raccoglie checklist e matrice test. Le voci sono formulate in modo prudenziale: indicano controlli da completare o verificare, non garanzie assolute.

## Checklist sicurezza

### Da completare prima del deploy condiviso

- Verificare permessi delle cartelle Drive.
- Limitare accesso al Limbo agli utenti autorizzati.
- Tenere segreti, token e webhook fuori dal codice.
- Verificare utenti autorizzati alla Web App.
- Definire cosa viene loggato e cosa non deve essere loggato.
- Verificare backup di Drive, Sheets e codice.
- Definire gestione degli allegati potenzialmente malevoli.
- Stabilire estensioni ammesse e vietate.
- Valutare quarantena o area di staging separata.
- Definire comportamento su errore parziale.
- Definire tempo di conservazione nel Limbo.
- Documentare procedura di recupero manuale.

### Da completare prima di usare AI su documenti reali

- Verificare DPA o accordi con il provider.
- Scegliere provider e regione dati.
- Chiarire se i dati sono usati per training.
- Definire localizzazione e conservazione dati.
- Stabilire anonimizzazione o pseudonimizzazione.
- Aggiornare registro trattamenti se necessario.
- Escludere categorie documentali non adatte.
- Rendere obbligatoria la revisione umana.
- Testare prima con dati fittizi o anonimizzati.
- Misurare costi API e limiti.

### Da completare prima del multi-utente

- Definire identita' e autorizzazioni.
- Separare ruoli utente, amministratore e manutentore.
- Stabilire audit minimo delle operazioni.
- Verificare permessi su ogni archivio condiviso.
- Decidere chi mantiene il sistema.
- Separare ambiente test e produzione.
- Definire procedura di onboarding e offboarding utenti.

## Allegati malevoli

Il salvataggio su Drive non deve essere considerato equivalente a una verifica completa di sicurezza. Un file puo' essere innocuo finche' resta non aperto, ma diventare rischioso se scaricato, sincronizzato, eseguito o aperto con software locale.

Contromisure da valutare:

- allowlist di estensioni;
- blocco di eseguibili, script, macro e archivi cifrati;
- Limbo non sincronizzato automaticamente sui client;
- accesso limitato al Limbo;
- naming che evidenzi stato "da verificare";
- procedura manuale per sbloccare o archiviare;
- configurazioni di sicurezza Google Workspace o Microsoft 365 disponibili.

## Matrice test

| ID | Funzione | Scenario | Input | Output atteso | Stato | Note |
|---|---|---|---|---|---|---|
| T01 | Virgilio | Apertura form | Accesso Web App | Form caricato | Da eseguire | Test manuale |
| T02 | Cartelle | Creazione pratica | Cliente, sito, anno, tipo | Cartella pratica creata | Da eseguire | Dati fittizi |
| T03 | Cartelle | Struttura trasversale | Sito senza sottocartelle | Cartelle standard presenti | Da eseguire | Verificare Adamo |
| T04 | Limbo | Salvataggio allegato | Email con PDF > 5 KB | File nel Limbo | Da eseguire | Gmail v1.0 |
| T05 | Limbo | Spostamento allegati | Pratica aperta dopo staging | File in corrispondenza | Da eseguire | Rischio matching temporale |
| T06 | Allegati | File piccolo | Immagine firma | File scartato | Da eseguire | Verifica filtro |
| T07 | Allegati | File grande | Allegato oltre limite | File scartato e log errore | Da eseguire | Limite configurato |
| T08 | Allegati | File sospetto | Estensione da definire | Comportamento da decidere | Futuro | Richiede policy |
| T09 | Gmail | Mono-utente | Etichetta `da-traghettare` | Thread elaborato se almeno un file salvato | Da eseguire | Solo esecutore |
| T10 | Notifiche | Google Chat | Pratica aperta | Messaggio inviato o errore non bloccante | Da eseguire | No token in log |
| T11 | Notifiche | Telegram | Pratica aperta | Messaggio inviato o errore non bloccante | Da eseguire | HTML escapato |
| T12 | Errori | Webhook Chat errato | URL non valido | Operazione principale continua | Da eseguire | Log errore |
| T13 | Errori | Telegram errato | Token/chat non validi | Operazione principale continua | Da eseguire | Log errore |
| T14 | Errori | Drive non raggiungibile | ID cartella errato | Errore gestito | Da eseguire | Non usare dati reali |
| T15 | Errori | Bucoliche non raggiungibile | ID foglio errato | Operazione principale da verificare | Da eseguire | Comportamento attuale tollerante |
| T16 | Cartelle | Assenza cartella | Adamo non raggiungibile | Fallback o errore documentato | Da eseguire | Dipende dal caso |
| T17 | Pratica | Duplicazione pratica | Stesso cliente/sito/tipo/anno | Cartella esistente riusata | Da eseguire | Verificare log |
| T18 | Ripristino | Rollback manuale | Errore dopo creazione | Procedura documentata | Futuro | Da definire |
| T19 | Multi-utente | Due utenti | Due caselle | Nessun blocco reciproco | Futuro | Non implementato |
| T20 | Workspace Studio | Flow | Email con allegato | Valutazione fattibilita' | Futuro | Non implementato |
| T21 | VTEnext | Webhook | Payload pratica | Flusso da definire | Futuro | Non implementato |
| T22 | AI | Classificazione | Dati fittizi | Suggerimento non operativo | Futuro | Revisione umana |

## Criteri pre-deploy condiviso

Prima di allargare il prototipo:

- completare test T01-T17 con dati fittizi;
- decidere D01, D03, D04, D08, D10 e D12;
- documentare procedura di incidente;
- verificare permessi reali con almeno due utenti pilota;
- mantenere possibilita' di rollback alla v1.0.
