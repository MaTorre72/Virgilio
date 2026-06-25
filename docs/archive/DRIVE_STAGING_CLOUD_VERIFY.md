# Verifica cloud read-only dello staging Drive Desktop

## Scopo

Verificare che un file e il relativo manifest, copiati dal Local Connector nella
cartella locale sincronizzata da Google Drive Desktop, siano diventati visibili
nella cartella Drive `Limbo_Test_Local`.

La verifica non prende in carico il documento: cerca due nomi, legge metadati Drive
e apre soltanto il manifest JSON per confrontarne i campi minimi.

## Stati distinti

| Stato | Evidenza disponibile |
|---|---|
| `staged_local_drive` | File e manifest presenti nella cartella locale configurata |
| `cloud_visible` | Apps Script vede entrambi su Drive e il manifest e' coerente |

`cloud_visible` e' un esito della risposta dry-run, non uno stato operativo SQLite.
Non implica archiviazione, registrazione Bucoliche o autorizzazione all'ack Gmail.

## Perche' e' read-only

Il ramo `verify_drive_staging` usa soltanto:

- `DriveApp.getFolderById`;
- `folder.getFilesByName`;
- `file.getSize`;
- `manifestFile.getBlob().getDataAsString` per il solo JSON manifest.

Non usa metodi per creare, copiare, spostare, rinominare, aggiornare o cancellare
file. Non chiama Gmail, Sheets o notifiche.

## Configurazione

L'ID reale della cartella non e' nel repository. Configurarlo una volta nelle
Script Properties eseguendo dall'editor Apps Script:

```javascript
caronteConfiguraCartellaStagingDriveTest('ID_CARTELLA_LIMBO_TEST_LOCAL');
```

La proprieta' salvata e' `VIRGILIO_DRIVE_STAGING_FOLDER_ID`. In alternativa puo'
essere inserita manualmente nelle impostazioni del progetto Apps Script.

Il client locale usa lo stesso URL `/exec` del bridge metadata-only, ma richiede
una variabile esplicita:

```dotenv
VIRGILIO_CARONTE_DRIVE_VERIFY_URL=https://script.google.com/macros/s/.../exec
```

## Payload

```json
{
  "action": "verify_drive_staging",
  "dry_run": true,
  "attachment_id": "att-opaque",
  "staged_filename": "att-opaque-document.pdf",
  "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "size_bytes": 1234
}
```

Il payload non contiene path locale, byte, base64, credenziali o contenuto file.

## Limiti

- ricerca limitata alla cartella configurata, non ricorsiva;
- nomi duplicati sono trattati come errore;
- l'hash del file Drive non viene ricalcolato: viene confrontato quello nel manifest;
- viene controllata la dimensione metadata del file;
- nessuna registrazione persistente dell'esito cloud;
- nessuna garanzia che Drive Desktop abbia terminato ogni sincronizzazione futura.

## Rischi residui

- file e manifest possono diventare visibili in momenti diversi;
- account Apps Script e Drive Desktop possono puntare a Drive diversi;
- cartella errata o non condivisa produce un falso “non visibile”;
- il deployment Web App resta un endpoint di test da proteggere in una fase futura;
- il manifest contiene metadati documentali e deve restare nel perimetro autorizzato.

## Test

`testDriveStagingCloudVerify()` usa folder e file finti in memoria e copre presenza,
assenze e payload incoerenti senza toccare Drive reale. I test Python usano HTTP
simulato e non eseguono rete.

## Controlli manuali

- attendere che Drive Desktop indichi sincronizzazione completata;
- verificare nella UI Drive la presenza di file e manifest;
- controllare che siano nella sola cartella `Limbo_Test_Local`;
- eseguire una singola verifica CLI;
- confermare che non siano apparse righe Bucoliche, notifiche o modifiche Gmail;
- non spostare o cancellare automaticamente i file dopo la verifica.

## Prossima fase

Documentare un test E2E read-only con un solo manifest. Soltanto dopo tale esito
decidere se e come Caronte possa prendere in carico file dal Limbo di test, con
idempotenza e rollback espliciti.
