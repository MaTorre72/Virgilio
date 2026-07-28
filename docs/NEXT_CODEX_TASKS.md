# Next Codex Task

## CORRENTE - CONS-R02 - README e changelog release 1.1

Stato: `TODO`. Priorita`: `P0`.

Risultato: README e changelog descrivono la release ufficiale 1.1, il percorso
utente realmente collaudato e i limiti operativi correnti senza dettagli obsoleti.

Dipendenze: `CONS-R01` chiuso `DONE`.

Componenti ammessi: README, changelog ufficiale e link/documentazione
strettamente necessari a renderli coerenti.

Esclusioni: codice, nuova build, tag, release remota, Apps Script, servizi reali,
riscrittura dei runbook e modifica di `main`.

Condizione di blocco: informazioni pubbliche indispensabili contraddittorie e
non risolvibili dalle evidenze correnti senza una decisione umana.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-R02-AC1` README presenta il percorso utente 1.1 corrente. | verifica sezioni e link |
| `CONS-R02-AC2` changelog ufficiale riassume funzioni e correzioni pubblicate. | confronto con stato collaudato |
| `CONS-R02-AC3` prerequisiti e limiti reali sono espliciti e coerenti. | ricerca termini e riferimenti |
| `CONS-R02-AC4` storico RC resta distinguibile dalla release ufficiale. | ricerca versioni e formulazioni |
| `CONS-R02-AC5` tree, segreti e puntatori sono coerenti. | diff, scansione e stato Git |

## SUCCESSIVO

`CONS-R03` - build release, installer, manifest e checksum dal commit candidato.
