# Test plan placeholder

Non sono presenti test eseguibili perche' questa fase non contiene ancora logica applicativa.

La prossima micro-fase dovra' introdurre test isolati e senza rete per:

- validazione del contratto JSON;
- nomi file sicuri;
- hash SHA-256;
- transizioni di stato della quarantena;
- idempotenza del `command_id` a livello di modello;
- regola di ack basata sulla risposta di Caronte.

I test non dovranno usare mailbox, credenziali, Drive, Bucoliche o allegati reali.
