# Backlog di sviluppo

Le fonti operative sono `docs/CODEX_STATE.md` e `docs/NEXT_CODEX_TASKS.md`;
l'ordine completo del consolidamento e` in `docs/CONSOLIDATION_PROGRAM.md`.
Lo storico di sviluppo e` condensato in `CHANGELOG.md` e registrato
cronologicamente in `docs/CHANGELOG_DEV.md`.

## Programma CONS - Pubblicazione, pulizia e consegna 1.1

Stato: `IN_PROGRESS`.

| Task | Stato | Evidenza sintetica |
| --- | --- | --- |
| `CONS-R01` | `DONE` | versione prodotto unica `1.1.0`; mirati `22 passed`, smoke `600 passed` |
| `CONS-R02` | `DONE` | README e changelog ufficiale 1.1 verificati; smoke `600 passed` |
| `CONS-R03` | `DONE` | installer ufficiale verificato, SHA-256 e Build ID registrati |
| `CONS-R04` | `DONE` | tag annotato `v1.1.0` pubblicato e verificato |
| `CONS-D01` | `DONE` | inventario documentale completo |
| `CONS-D02` | `DONE` | architettura corrente resa canonica |
| `CONS-D03` | `DONE` | runbook correnti brevi e verificati |
| `CONS-D04` | `DONE` | storia 1.1 condensata; fascicoli chiusi ritirati dal percorso corrente |
| `CONS-G01` | `DONE` | inventario di entry point, comandi, import e file di build |
| `CONS-G02` | `DONE` | GUI legacy e test esclusivi rimossi; target supportati verdi |
| `CONS-G03` | `DONE` | spike AI/LiteLLM/Docling e superfici esclusive rimossi |
| `CONS-G04` | `DONE` | 4 asset/script storici ritirati; mirati `26 passed`, smoke `533 passed` |

I task successivi restano chiusi finche` non diventano il successore immediato
in `docs/NEXT_CODEX_TASKS.md`; non vengono duplicati qui.

### Evidenze CONS-G04

| Criterio | Evidenza ottenuta | Esito |
| --- | --- | --- |
| `AC1` | inventario e ricerca statica: 2 probe standalone e 2 immagini 1.0 senza riferimenti correnti | `PASS` |
| `AC2` | `git cat-file` conferma recuperabilita` `4/4` dal commit precedente | `PASS` |
| `AC3` | riferimenti correnti `0`; test packaging/build/CLI mirati `26 passed` | `PASS` |
| `AC4` | immagini correnti e strumenti `scripts/dev` preservati; contratti mirati verdi | `PASS` |
| `AC5` | smoke locale `533 passed`; diff, segreti e puntatori verificati | `PASS` |
