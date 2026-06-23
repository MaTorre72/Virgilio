# Test suite

La suite usa soltanto `unittest` e dati sintetici.

Copertura attuale:

- validazione e round-trip del contratto JSON;
- blocco di campi inattesi e payload operativi non confermati;
- sanitizzazione nomi e SHA-256;
- policy iniziale sulle estensioni;
- transizioni valide e non valide della quarantena;
- regola di ack dopo conferma del Limbo Drive;
- verifica statica dell'assenza di import di rete.

La suite non usa mailbox, credenziali, Drive, Bucoliche o allegati reali.
