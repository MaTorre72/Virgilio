# Next Codex Task

## CORRENTE - CONS-D01 - Inventario documentale

Stato: `TODO`. Priorita`: `P1`.

Risultato: ogni documento versionato e` classificato senza ambiguita` come
`KEEP`, `MERGE`, `HISTORY` o `REMOVE`, con destinazione o motivazione esplicita.

Dipendenze: `CONS-R04` chiuso `DONE`; tag release `v1.1.0` pubblicato e verificato.

Componenti ammessi: documenti versionati, inventario documentale ed evidenze del
solo task.

Esclusioni: rimozione o fusione effettiva di file, codice, Apps Script, servizi
reali, modifica o merge di `main`.

Condizione di blocco: perimetro documentale non enumerabile, classificazione
ambigua senza fonte autorevole o upstream divergente.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-D01-AC1` ogni documento versionato compare una sola volta. | elenco Git e confronto inventario |
| `CONS-D01-AC2` ogni voce usa una delle quattro classi ammesse. | validazione categorie |
| `CONS-D01-AC3` `MERGE` e `REMOVE` indicano destinazione o motivazione. | controllo campi obbligatori |
| `CONS-D01-AC4` documenti canonici e storici sono distinguibili. | confronto link e fonti operative |
| `CONS-D01-AC5` inventario, diff, segreti e puntatori sono verificati. | controlli Git e scansione |

## SUCCESSIVO

`CONS-D02` - architettura corrente unificata in un solo documento canonico.
