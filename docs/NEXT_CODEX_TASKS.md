# Next Codex Task

## CORRENTE - CONS-D02 - Architettura corrente canonica

Stato: `TODO`. Priorita`: `P1`.

Risultato: l'architettura corrente e` descritta senza contraddizioni in
`docs/ARCHITETTURA_UNIFICATA.md`, unica fonte canonica.

Dipendenze: `CONS-D01` chiuso `DONE`; inventario documentale completo.

Componenti ammessi: `docs/ARCHITETTURA_UNIFICATA.md`, documenti classificati
`MERGE` verso l'architettura, link ed evidenze del solo task.

Esclusioni: rimozione di file, modifica funzionale di codice o Apps Script,
servizi reali, modifica o merge di `main`.

Condizione di blocco: contraddizione non risolvibile dalla baseline collaudata o
upstream divergente.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-D02-AC1` componenti e confini correnti sono univoci. | confronto con baseline e inventario |
| `CONS-D02-AC2` flusso end-to-end e contratti condivisi sono coerenti. | ricerca termini e link |
| `CONS-D02-AC3` GUI utente, manutenzione, CLI e GAS hanno responsabilita` distinte. | verifica sezioni canoniche |
| `CONS-D02-AC4` i documenti architetturali `MERGE` non restano fonti concorrenti. | confronto e aggiornamento link |
| `CONS-D02-AC5` diff, segreti, prove e puntatori sono verificati. | controlli Git e documentali |

## SUCCESSIVO

`CONS-D03` - runbook brevi per setup, sviluppo, test, operazioni e release.
