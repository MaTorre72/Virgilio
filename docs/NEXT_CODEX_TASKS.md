# Next Codex Task

## CORRENTE - CONS-C03 - Parser e dispatch separati dal bootstrap

Stato: `TODO`. Priorita`: `P1`.

Risultato: `__main__` resta un bootstrap minimo mentre costruzione del parser e
dispatch CLI sono separati per responsabilita`, senza cambiare output, codici di
uscita o comportamento dei comandi conservati.

Dipendenze: `CONS-C02` chiuso `DONE`; classificazione e help intenzionale
registrati in `docs/SURFACE_INVENTORY.md`.

Componenti ammessi: bootstrap `__main__`, parser/dispatch CLI, test di
caratterizzazione per gruppo e relativi puntatori.

Esclusioni: modifica della classificazione o semantica dei comandi,
implementazioni operative, GUI, servizi reali, deploy, modifica o merge di
`main`.

Condizione di blocco: non e` possibile preservare un contratto CLI osservabile
con test di caratterizzazione oppure upstream diverge.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-C03-AC1` il bootstrap contiene solo composizione e uscita. | ispezione struttura e test import |
| `CONS-C03-AC2` la costruzione del parser e` isolata e conserva l'help. | snapshot help |
| `CONS-C03-AC3` il dispatch e` separato per gruppi coerenti. | test comando per gruppo |
| `CONS-C03-AC4` output, errori e codici di uscita restano invariati. | test di caratterizzazione CLI |
| `CONS-C03-AC5` suite richiesta, diff, segreti e puntatori sono verificati. | test a scalare e controlli Git |

## SUCCESSIVO

`CONS-C04` - primo modulo operativo monolitico separato per responsabilita`.
