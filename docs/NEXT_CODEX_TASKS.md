# Next Codex Task

## CORRENTE - CONS-C02 - Comandi CLI classificati

Stato: `TODO`. Priorita`: `P1`.

Risultato: ogni comando CLI e` classificato come supportato, interno o da
rimuovere, con help coerente e senza cambiare il comportamento supportato.

Dipendenze: `CONS-C01` chiuso `DONE`; dispatch inventariato in
`docs/SURFACE_INVENTORY.md`.

Componenti ammessi: parser/dispatch CLI, snapshot help, test CLI e relativi
puntatori.

Esclusioni: implementazioni operative, nuova funzionalita`, GUI, servizi reali,
deploy, modifica o merge di `main`.

Condizione di blocco: la classificazione richiede una decisione di prodotto non
documentata oppure upstream diverge.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-C02-AC1` ogni comando e` classificato con motivazione. | inventario dispatch aggiornato |
| `CONS-C02-AC2` l'help mostra soltanto la superficie intenzionale. | snapshot help |
| `CONS-C02-AC3` comandi interni restano raggiungibili solo dagli ingressi necessari. | test dispatch mirati |
| `CONS-C02-AC4` comandi non supportati sono rimossi senza cambiare quelli supportati. | ricerca e test CLI |
| `CONS-C02-AC5` suite richiesta, diff, segreti e puntatori sono verificati. | test a scalare e controlli Git |

## SUCCESSIVO

`CONS-C03` - parser e dispatch CLI separati dal bootstrap `__main__`.
