# Next Codex Task

## CORRENTE - CONS-R04 - Tag release v1.1.0

Stato: `TODO`. Priorita`: `P0`.

Risultato: il tag annotato `v1.1.0` identifica senza ambiguita` il commit release
e il riferimento remoto coincide con quello locale.

Dipendenze: `CONS-R03` chiuso `DONE`; installer e manifest verificati dal commit
`68f3b90`.

Componenti ammessi: tag Git annotato `v1.1.0`, riferimenti remoti ed evidenze
documentali del solo task.

Esclusioni: release GitHub, Apps Script, servizi reali, modifica o merge di
`main`, altri tag e cambiamenti funzionali.

Condizione di blocco: tag locale o remoto preesistente, commit candidato mutato,
upstream divergente o impossibilita` di verificare il riferimento remoto.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-R04-AC1` nessun `v1.1.0` locale o remoto preesiste. | elenco tag e `ls-remote` |
| `CONS-R04-AC2` il commit candidato coincide con branch e manifest release. | confronto SHA |
| `CONS-R04-AC3` il tag annotato contiene identita` e riferimenti release. | `git show` del tag |
| `CONS-R04-AC4` il push crea solo `refs/tags/v1.1.0`. | push esplicito e fetch |
| `CONS-R04-AC5` riferimenti locale/remoto, tree e puntatori coincidono. | rev-parse, diff e stato Git |

## SUCCESSIVO

`CONS-D01` - inventario documentale `KEEP/MERGE/HISTORY/REMOVE` completo.
