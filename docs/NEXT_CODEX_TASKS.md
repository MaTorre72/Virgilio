# Next Codex Task

## CORRENTE - CONS-C01 - API intenzionali e fonte versione unica

Stato: `TODO`. Priorita`: `P1`.

Risultato: `virgilio_connector.__init__` espone soltanto API pubbliche
intenzionali e usa la fonte versione autorevole gia` definita.

Dipendenze: `CONS-G04` chiuso `DONE`; inventario degli import diretti disponibile
in `docs/SURFACE_INVENTORY.md`.

Componenti ammessi: `local_connector/src/virgilio_connector/__init__.py`, fonte
versione, test del contratto import e relativi puntatori.

Esclusioni: implementazioni operative, dispatch CLI, comportamento runtime,
nuova funzionalita`, servizi reali, deploy, modifica o merge di `main`.

Condizione di blocco: un simbolo candidato alla rimozione e` un contratto
pubblico intenzionale o un import supportato, oppure upstream diverge.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-C01-AC1` le API pubbliche intenzionali sono elencate e motivate. | inventario import e contratto esplicito |
| `CONS-C01-AC2` riesportazioni interne o accidentali sono rimosse senza cambiare implementazioni. | diff del package root e ricerca import |
| `CONS-C01-AC3` versione package, metadata e runtime provengono dalla stessa fonte. | test versione e metadata |
| `CONS-C01-AC4` import supportati e ingressi conservano i contratti. | test import/CLI/build mirati |
| `CONS-C01-AC5` suite richiesta, diff, segreti e puntatori sono verificati. | test a scalare e controlli Git |

## SUCCESSIVO

`CONS-C02` - comandi CLI classificati supportati, interni o rimossi.
