# Setup e test

## Setup locale

```powershell
cd C:\Users\Marco\Documents\Virgilio
.\.venv\Scripts\python.exe -m pip install -e .\local_connector
```

Configurazioni reali devono stare solo in `.env`, mai nel repository.

## Test Python

```powershell
.\.venv\Scripts\python.exe -m pytest local_connector
```

I test automatici devono restare offline: niente Gmail reale, Drive reale, Bucoliche reale, notifiche o credenziali.

## Test Apps Script

Eseguire solo test puri o mockabili dall'editor Apps Script. I test che richiedono Drive, Gmail, Bucoliche o deployment reale vanno trattati come collaudi manuali separati.

## Collaudi reali

Ogni collaudo reale deve indicare:

- branch e commit;
- account/cartella di test;
- comando eseguito;
- risposta ricevuta;
- conferma degli effetti non prodotti;
- checklist manuale finale.
