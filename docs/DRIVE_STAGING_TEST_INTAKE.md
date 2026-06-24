# Presa in carico di test dello staging Drive

## Scopo

Questa fase registra che Caronte ha trovato e validato un file staged e il suo
manifest nella cartella Drive di test. `cloud_visible` prova soltanto la
visibilità; `presa_in_carico_test` aggiunge una riga di audit nel tab test.
Non è archiviazione: file e manifest restano fermi nello staging.

## Destinazione e configurazione

La soluzione scelta è il tab `Staging_Local_Test` nello spreadsheet Bucoliche,
separato dal tab operativo. Gli identificativi sono esclusivamente Script
Properties:

- `VIRGILIO_INTAKE_TEST_SPREADSHEET_ID`
- `VIRGILIO_INTAKE_TEST_SHEET_NAME`

Il tab viene creato soltanto eseguendo esplicitamente
`caronteSetupStagingDriveTestIntake(spreadsheetId, sheetName)`. Dall'editor la
funzione può essere eseguita senza argomenti dopo avere impostato le due Script
Properties. L'intake non crea tab e rifiuta un nome uguale al tab Bucoliche reale.

## Scrittura

Una riga contiene timestamp, origine e account, riferimenti al messaggio,
metadati allegato/scansione, esiti di verifica, ID Drive dei due oggetti, stato
`presa_in_carico_test` e note. Apps Script legge il JSON del manifest e i soli
metadati del PDF; non legge o scarica il PDF.

Non vengono eseguiti spostamenti, copie o cancellazioni Drive, scritture nel tab
reale, notifiche, operazioni Gmail/IMAP, retention o archiviazione pratica.

## Flusso

1. verificare `cloud_visible=true`;
2. eseguire il setup esplicito del tab una sola volta;
3. configurare `VIRGILIO_CARONTE_INTAKE_TEST_URL` con lo stesso `/exec`;
4. inviare un manifest con `intake-drive-staging-test`;
5. controllare una sola nuova riga nel tab test.

## Rischi e rollback

Rischi residui: doppia esecuzione manuale, permessi spreadsheet e modifica
accidentale delle Script Properties. Il rollback è manuale: eliminare la riga
test (o l'intero tab test) e rimuovere le due proprietà. Non cancellare i file
staged come parte del rollback di questa fase.

## Idempotenza della presa in carico test

L'idempotenza impedisce che un retry dello stesso comando produca più righe.
La chiave primaria è `attachment_id`, cercata esattamente nella colonna 6 del
tab test; la colonna 9 (`sha256`) è il controllo aggiuntivo di coerenza.

- stesso `attachment_id` e stesso SHA-256: nessuna append, risposta
  `already_registered=true`, `idempotent=true` ed `existing_row` valorizzato;
- stesso `attachment_id` e SHA-256 diverso: richiesta rifiutata con
  `ATTACHMENT_SHA256_CONFLICT`, senza scritture;
- `attachment_id` assente o non valido: validazione fallita prima della ricerca.

Non vengono ancora aggiornate righe esistenti, rimossi file, applicata retention,
eseguiti spostamenti o effettuata una presa in carico operativa.
