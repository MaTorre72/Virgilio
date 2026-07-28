# Next Codex Task

## CORRENTE - CONS-H02 - Audit finale del consolidamento

Stato: `TODO`. Priorita`: `P1`.

Risultato: struttura, documentazione, segreti, suite, build e release sono
verificati insieme contro lo stato consolidato 1.1, senza modifiche funzionali.

Dipendenze: `CONS-H01` chiuso `DONE`; onboarding fresh-clone e smoke sono
ripetibili.

Componenti ammessi: inventari e documenti correnti, controlli Git, suite
offline, pipeline di build e metadati della release pubblicata.

Esclusioni: nuove funzionalita`, servizi reali, credenziali, deploy, modifica o
merge di `main`.

Condizione di blocco: un gate finale non e` riproducibile o contraddice la
release pubblicata, oppure upstream diverge.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-H02-AC1` struttura e superfici correnti coincidono con gli inventari. | audit repository |
| `CONS-H02-AC2` documenti correnti, link e puntatori sono coerenti. | audit documentale |
| `CONS-H02-AC3` file vietati e segreti versionati sono assenti. | scansione Git |
| `CONS-H02-AC4` suite offline e build consolidate sono verdi. | smoke e build |
| `CONS-H02-AC5` versione, tag, installer e checksum pubblicati coincidono. | audit release |

## SUCCESSIVO

`CONS-H03` - branch pubblicata e pull request verso `main` pronta per revisione umana.

## EVIDENZA CONS-H01

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| --- | --- | --- | --- |
| `CONS-H01-AC1` | revisione guida | prerequisiti e sequenza unica clone/bootstrap/help/smoke in `RUNBOOKS.md` | `PASS` |
| `CONS-H01-AC2` | ambiente isolato | bootstrap crea il venv e installa `local_connector[dev]` dalla sola dichiarazione `pyproject.toml` | `PASS` |
| `CONS-H01-AC3` | prova fresh clone | clone locale isolato, bootstrap e help completati senza configurazioni o credenziali | `PASS` |
| `CONS-H01-AC4` | smoke fresh clone | ambiente appena creato: `548 passed`, help CLI e controlli repository verdi | `PASS` |
| `CONS-H01-AC5` | controlli Git | test contratto `2 passed`; diff, segreti e puntatori verificati | `PASS` |
