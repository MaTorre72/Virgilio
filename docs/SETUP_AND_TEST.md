# Setup e test

## Setup locale

```powershell
cd C:\Users\Marco\Documents\Virgilio
.\.venv\Scripts\python.exe -m pip install -e .\local_connector
```

Configurazioni reali devono stare solo in `.env`, mai nel repository.

Per creare uno scheletro locale valido senza segreti nel file:

```powershell
virgilio init-config --output accounts.local.yaml --email nome@azienda.it --staging-dir C:\Virgilio\staging
```

Il comando genera un `accounts.local.yaml` con account, storage, Bucoliche e rules minime;
le credenziali restano solo come nomi di variabili d'ambiente da valorizzare localmente.

## Test Python

```powershell
.\.venv\Scripts\python.exe -m pytest local_connector
```

I test automatici devono restare offline: niente Gmail reale, Drive reale, Bucoliche reale, notifiche o credenziali.

## Test Apps Script

Eseguire solo test puri o mockabili dall'editor Apps Script. I test che richiedono Drive, Gmail, Bucoliche o deployment reale vanno trattati come collaudi manuali separati.

## Collaudi reali

I percorsi che escono dal dry-run (`pilot-run` senza `--dry-run` e, nel profilo Google-only, `clasp push`) sono collaudi reali, non test automatici.

Ogni collaudo reale deve indicare:

- branch e commit;
- account/cartella di test;
- comando eseguito;
- risposta ricevuta;
- conferma degli effetti non prodotti;
- checklist manuale finale.
