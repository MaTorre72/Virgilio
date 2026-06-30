# Test suite

La suite usa soltanto `unittest` e dati sintetici.

Copertura attuale:

- validazione e round-trip del contratto JSON;
- blocco di campi inattesi e payload operativi non confermati;
- sanitizzazione nomi e SHA-256;
- policy iniziale sulle estensioni;
- transizioni valide e non valide della quarantena;
- regola di ack dopo conferma del Limbo Drive;
- confinamento degli import di rete e adapter IMAP simulato;
- garanzia read-only: `SELECT readonly=True`, `BODY.PEEK[]`, nessun comando mutante.
- rilevazione di `conflict_cross_machine` senza risoluzione automatica; la procedura
  operativa manuale e' documentata in `docs/BUCOLICHE_CONFLICT_POLICY.md`.

La suite automatica non usa mailbox, credenziali, Drive, Bucoliche o allegati reali.
