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
| `CONS-G01` | `TODO` | inventario di entry point, comandi, import e file di build |

I task successivi restano chiusi finche` non diventano il successore immediato
in `docs/NEXT_CODEX_TASKS.md`; non vengono duplicati qui.

### Evidenze CONS-D04

| Criterio | Evidenza ottenuta | Esito |
| --- | --- | --- |
| `AC1` | `CHANGELOG.md` conserva funzioni, correzioni, baseline `7e18277`, `PASS` umano e deployment `40` | `PASS` |
| `AC2` | backlog corrente ridotto a CONS; fascicoli chiusi assenti dal tree corrente | `PASS` |
| `AC3` | riferimenti esclusivamente storici verificati; 17 file recuperabili da `45a19f4` | `PASS` |
| `AC4` | README, runbook e puntatori operativi non collegano i fascicoli ritirati | `PASS` |
| `AC5` | inventario, link, diff e segreti verificati; smoke locale `600 passed` | `PASS` |
