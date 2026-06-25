# Roadmap v1.1

## A. Cleanup e consolidamento

Consolidare branch stabili, ridurre documentazione, tenere fuori i rami sperimentali superati.

## B. Multi-account IMAP

Introdurre configurazione locale per piu' caselle, con isolamento stato, log e quarantena.

## C. Ack IMAP locale

Definire ack esplicito e reversibile: solo dopo presa in carico riuscita, stato coerente e policy approvata.

## D. Registro SQLite e Bucoliche adapter

Usare SQLite come registro primario. Bucoliche diventa output adapter opzionale e idempotente.

## E. Storage adapter cartelle pratica

Astrarre lo storage finale: cartelle locali, Drive Desktop, Drive API o altro adapter.

## F. Notifiche adapter

Isolare Chat, Telegram o email come notifiche opzionali, mai bloccanti per lo stato primario.

## G. Pilota 2 utenti

Eseguire pilota controllato con due utenti, caselle dedicate, dati non critici e checklist di rollback.
