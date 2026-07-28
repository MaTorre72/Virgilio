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
| `CONS-C01` | `DONE` | root API limitata a `__version__`; mirati `17 passed`, smoke `535 passed` |
| `CONS-C03` | `DONE` | bootstrap minimo e parser/dispatch isolati; area CLI `173 passed` |

I task successivi restano chiusi finche` non diventano il successore immediato
in `docs/NEXT_CODEX_TASKS.md`; non vengono duplicati qui.

### Evidenze CONS-C01

| Criterio | Evidenza ottenuta | Esito |
| --- | --- | --- |
| `AC1` | inventario motivato: solo `__version__` e` API stabile del root | `PASS` |
| `AC2` | rimosse le riesportazioni operative; nessun import diretto corrente dipende da esse | `PASS` |
| `AC3` | root, metadata e build puntano a `_version.__version__`; test versione verdi | `PASS` |
| `AC4` | moduli `__main__`, `build_entry`, `maintenance_gui` e `user_app` importabili | `PASS` |
| `AC5` | test mirati `17 passed`, smoke locale `535 passed`; diff, segreti e puntatori verificati | `PASS` |

### Evidenze CONS-C03

| Criterio | Evidenza ottenuta | Esito |
| --- | --- | --- |
| `AC1` | `__main__.py` contiene solo composizione, compatibilita` import e uscita | `PASS` |
| `AC2` | `cli.build_parser()` isolato; snapshot help e rifiuto alias verdi | `PASS` |
| `AC3` | dispatch separato dal parser; rappresentanti di cinque gruppi registrati | `PASS` |
| `AC4` | test esistenti su output, errori e codici di uscita invariati | `PASS` |
| `AC5` | area CLI `173 passed`; smoke locale `543 passed`; diff, segreti e puntatori verificati | `PASS` |
