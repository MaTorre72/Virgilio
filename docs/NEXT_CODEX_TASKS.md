# Next Codex Task

## CORRENTE - CONS-G03 - Rimozione spike sperimentali

Stato: `TODO`. Priorita`: `P1`.

Risultato: spike AI, LiteLLM, Docling e superfici sperimentali non supportate
sono rimossi senza modificare i percorsi documentali e operativi supportati.

Dipendenze: `CONS-G02` chiuso `DONE`; inventario delle superfici disponibile in
`docs/SURFACE_INVENTORY.md`.

Componenti ammessi: spike AI/LiteLLM/Docling, parser e dispatch sperimentali,
test e riferimenti esclusivi, inventario e test CLI/import mirati.

Esclusioni: nuova funzionalita`, sostituzioni AI, refactor dei percorsi
supportati, servizi reali, build/deploy reale, modifica o merge di `main`.

Condizione di blocco: un percorso supportato dipende da una superficie
sperimentale, un test esclusivo copre un contratto corrente non trasferibile, o
upstream divergente.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-G03-AC1` nessun target supportato dipende dagli spike. | inventario G01 e ricerca statica |
| `CONS-G03-AC2` moduli, comandi e test esclusivi sono rimossi e recuperabili da Git. | elenco target, storia e ricerca riferimenti |
| `CONS-G03-AC3` CLI e percorsi supportati conservano import e contratti. | test CLI/import mirati |
| `CONS-G03-AC4` dipendenze e packaging non includono AI/LiteLLM/Docling. | metadata, build test e ricerca statica |
| `CONS-G03-AC5` suite richiesta, diff, segreti e puntatori sono verificati. | test a scalare e controlli Git |

## SUCCESSIVO

`CONS-G04` - asset e script storici non necessari rimossi o spostati nelle release.
