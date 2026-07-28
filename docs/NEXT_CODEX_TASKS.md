# Next Codex Task

## CORRENTE - CONS-R03 - Build release 1.1.0

Stato: `TODO`. Priorita`: `P0`.

Risultato: installer, manifest e checksum della release ufficiale `1.1.0` sono
prodotti dal commit candidato e superano gli smoke previsti.

Dipendenze: `CONS-R02` chiuso `DONE`.

Componenti ammessi: pipeline di build e release, artefatti locali ignorati,
manifest, checksum e documentazione delle sole evidenze del task.

Esclusioni: tag, release remota, Apps Script, servizi reali, modifica o merge di
`main` e cambiamenti funzionali.

Condizione di blocco: build non riproducibile dal commit pulito o prerequisito
locale indispensabile assente e non ripristinabile senza decisione umana.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-R03-AC1` build parte dal commit candidato pulito e identifica `1.1.0`. | manifest e build-info |
| `CONS-R03-AC2` installer ufficiale e` prodotto con nome e payload coerenti. | smoke build |
| `CONS-R03-AC3` installazione controllata supera lo smoke senza perdita dati. | smoke installer |
| `CONS-R03-AC4` SHA-256, dimensione, commit e Build ID sono registrati. | confronto artefatto/manifest |
| `CONS-R03-AC5` tree, segreti e puntatori sono coerenti. | diff, scansione e stato Git |

## SUCCESSIVO

`CONS-R04` - tag annotato `v1.1.0` e relativi riferimenti remoti verificati.
