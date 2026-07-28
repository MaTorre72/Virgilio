# Next Codex Task

## CORRENTE - CONS-R01 - Versione prodotto unica 1.1.0

Stato: `TODO`. Priorita`: `P0`.

Risultato: il prodotto pubblicabile usa una sola versione `1.1.0`; la stringa
`0.11.0` resta soltanto nelle evidenze storiche delle RC gia` collaudate.

Dipendenze: `GUI-U-R05` e `GATE U-H3` chiusi `PASS` il 2026-07-28.

Componenti ammessi: `VERSION`, package metadata/versione, manifest e script di
build, test mirati sulla versione e documentazione strettamente coinvolta.

Esclusioni: cambiamenti funzionali, refactor, nuova build reale, tag, release,
Apps Script, servizi reali e modifica di `main`.

Condizione di blocco: impossibilita` di mantenere compatibilita` dell'installer o
di ricavare tutte le identita` di build da una fonte autorevole senza cambiare il
runtime collaudato.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-R01-AC1` `1.1.0` e` la sola versione corrente nei sorgenti. | ricerca repository con esclusione esplicita di storico/evidenze |
| `CONS-R01-AC2` package e build leggono una sola fonte autorevole. | test metadata e manifest |
| `CONS-R01-AC3` Informazioni e `--build-info` espongono `1.1.0`. | test mirati build-info/about |
| `CONS-R01-AC4` nessun comportamento operativo cambia. | diff circoscritto e test mirati |
| `CONS-R01-AC5` tree, segreti e puntatori sono coerenti. | diff, scansione e stato Git |

## SUCCESSIVO

`CONS-R02` - README e changelog della release ufficiale 1.1.
