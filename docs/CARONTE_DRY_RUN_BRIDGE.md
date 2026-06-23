# Caronte dry-run bridge

## Scopo

Verificare il collegamento di rete tra Local IMAP Connector e Caronte scambiando
soltanto metadati gia' validati. Questa fase non trasferisce allegati e non produce
effetti operativi.

## Flusso

1. Il connettore genera localmente un comando Caronte 1.0 con `dry_run=true`.
2. L'operatore configura l'URL Web App soltanto in `.env`.
3. Il client valida nuovamente il file e blocca campi vietati.
4. Viene eseguito un singolo POST con action `local_imap_dry_run`.
5. `doPost` instrada al ricevitore puro `caronteRiceviComandoDryRun`.
6. Il ricevitore restituisce conteggi ed errori, con liste Drive/Bucoliche vuote.

## Limiti e sicurezza

- Nessun multipart, base64, byte o percorso locale.
- Nessun retry automatico.
- Nessuna persistenza della risposta nel database locale.
- Nessun uso di DriveApp, SpreadsheetApp, GmailApp o servizi di notifica nel bridge.
- Il precedente ramo operativo di `doPost` resta invariato e continua a usare il
  proprio token.
- L'URL e le impostazioni di accesso al deploy non sono versionati. Prima della
  prova reale occorre valutare chi puo' invocare la Web App: il bridge non deve
  essere considerato un endpoint autenticato soltanto perche' non ha effetti.

## Test

Apps Script espone `testCaronteBridgeDryRun()`, test puro per payload valido,
attachments vuoto, dry-run falso, campi vietati e SHA-256 mancante.

Python usa mock HTTP per verificare URL assente, POST valido, timeout senza retry,
risposte positive/negative e blocco pre-rete dei campi vietati.

## Prossima fase

Distribuire una versione di test della Web App, configurare l'URL localmente ed
eseguire un solo comando sintetico. Prima di qualsiasi trasporto operativo vanno
progettati autenticazione, idempotenza, upload separato e rollback.
