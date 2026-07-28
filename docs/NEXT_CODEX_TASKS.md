# Next Codex Task

## CORRENTE - CONS-G02 - Rimozione GUI legacy

Stato: `TODO`. Priorita`: `P1`.

Risultato: l'implementazione abbandonata `gui`/`gui_*` e i test esclusivi sono
rimossi senza modificare GUI utente, nuova Manutenzione, CLI o build.

Dipendenze: `CONS-G01` chiuso `DONE`; inventario delle superfici disponibile in
`docs/SURFACE_INVENTORY.md`.

Componenti ammessi: moduli legacy `gui`/`gui_*`, test e riferimenti esclusivi,
inventario delle superfici e test GUI/build mirati.

Esclusioni: nuova funzionalita`, refactor dei target supportati, servizi reali,
build/deploy reale, modifica o merge di `main`.

Condizione di blocco: un target supportato importa il legacy, un test esclusivo
copre anche un contratto corrente non trasferibile, o upstream divergente.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-G02-AC1` nessun target supportato importa moduli legacy. | ricerca statica e inventario G01 |
| `CONS-G02-AC2` `gui.py`, `gui_*` e test esclusivi sono rimossi e recuperabili da Git. | elenco target, commit sorgente e ricerca riferimenti |
| `CONS-G02-AC3` GUI utente e nuova Manutenzione conservano ingressi e contratti. | test GUI mirati |
| `CONS-G02-AC4` CLI e configurazione build non includono riferimenti legacy. | help, test build e ricerca statica |
| `CONS-G02-AC5` suite richiesta, diff, segreti e puntatori sono verificati. | test a scalare e controlli Git |

## SUCCESSIVO

`CONS-G03` - spike AI/LiteLLM/Docling e superfici sperimentali non supportate rimossi.
