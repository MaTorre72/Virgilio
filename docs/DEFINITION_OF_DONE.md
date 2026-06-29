# Definition of Done

Un task è completato soltanto quando:

- scopo e criteri del task in `DEV_BACKLOG.md` sono soddisfatti;
- test mirati e suite `pytest local_connector` sono verdi;
- lo smoke test locale è verde;
- nessun segreto o dato operativo è tracciato;
- nessuna regressione dei comandi pilota è introdotta;
- documentazione minima e backlog sono aggiornati;
- storage, email e Google hanno dry-run e fake-client test;
- non sono avvenute chiamate reali non esplicitamente autorizzate;
- il commit è atomico, leggibile e il working tree è pulito;
- il riepilogo finale non supera 12 righe.

Un task bloccato resta non completato e riporta causa, evidenza e singola azione necessaria.

