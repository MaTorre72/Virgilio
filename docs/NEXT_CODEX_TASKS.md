# Next Codex Task

## CORRENTE - CONS-G04 - Pulizia asset e script storici

Stato: `TODO`. Priorita`: `P1`.

Risultato: asset e script storici non necessari sono rimossi oppure collocati
nelle release senza alterare build, test e operazioni supportate.

Dipendenze: `CONS-G03` chiuso `DONE`; inventario delle superfici disponibile in
`docs/SURFACE_INVENTORY.md`.

Componenti ammessi: asset generati o storici, script non raggiungibili, relativi
riferimenti, inventario e test di packaging/link mirati.

Esclusioni: codice operativo raggiungibile, artefatti ufficiali 1.1, nuova
funzionalita`, servizi reali, deploy, modifica o merge di `main`.

Condizione di blocco: un target candidato e` richiesto da build, test, runbook o
operazioni supportate, non e` recuperabile da Git/release, o upstream diverge.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-G04-AC1` ogni target rimosso e` storico, non raggiungibile e inventariato. | ricerca statica e inventario G01 |
| `CONS-G04-AC2` ogni rimozione e` recuperabile da Git o dalla release ufficiale. | storia e riferimenti release |
| `CONS-G04-AC3` build, test e runbook non conservano riferimenti rotti. | test packaging e controllo link |
| `CONS-G04-AC4` ingressi e operazioni supportati conservano i contratti. | test CLI/import mirati |
| `CONS-G04-AC5` suite richiesta, diff, segreti e puntatori sono verificati. | test a scalare e controlli Git |

## SUCCESSIVO

`CONS-C01` - `__init__.py` espone solo API intenzionali e una sola fonte versione.
