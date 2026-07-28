# Next Codex Task

## CORRENTE - CONS-H03 - Pull request finale verso main

Stato: `TODO`. Priorita`: `P1`.

Risultato: la branch consolidata e` pubblicata e una pull request verso `main`
presenta la release 1.1, le prove finali e i gate riservati alla revisione
umana, senza eseguire il merge.

Dipendenze: `CONS-H02` chiuso `DONE`; tutti i gate finali sono verdi.

Componenti ammessi: controlli Git e remoto, documentazione di handoff, branch
`codex/v1.1-development` e pull request verso `main`.

Esclusioni: nuove modifiche funzionali, servizi reali, credenziali, deploy,
force-push, modifica o merge di `main`, approvazione autonoma dei gate umani.

Condizione di blocco: branch divergente, upstream inatteso, gate finale non piu`
verde o impossibilita` di creare/verificare la pull request senza alterare
`main`.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-H03-AC1` HEAD locale e remoto della branch coincidono dopo il fetch finale. | confronto puntatori Git |
| `CONS-H03-AC2` handoff riassume programma, release, prove e rischi residui senza fonti concorrenti. | revisione documentale |
| `CONS-H03-AC3` pull request unica ha base `main`, head consolidata e descrizione verificabile. | verifica PR remota |
| `CONS-H03-AC4` stato finale e controlli della pull request sono pronti per revisione umana. | audit PR e check |
| `CONS-H03-AC5` `main` non e` modificata o unita e l'automazione viene messa in pausa. | verifica branch e automazione |

## SUCCESSIVO

Nessuno: `CONS-H03` chiude il programma `CONS`.

## EVIDENZA CONS-H02

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| --- | --- | --- | --- |
| `CONS-H02-AC1` | audit repository | 208 file tracciati; 44/44 documenti nell'ambito inventariato; superfici legacy vietate trovate: 0 | `PASS` |
| `CONS-H02-AC2` | audit documentale | smoke repository e controlli dei puntatori verdi; fonti correnti e inventari coerenti | `PASS` |
| `CONS-H02-AC3` | scansione Git | nessun segreto o file operativo vietato tracciato; il solo `.env.example` contiene valori sintetici | `PASS` |
| `CONS-H02-AC4` | smoke e build | smoke `548 passed`; build Caronte e installer 1.1.0 completata; smoke build e installer `OK` | `PASS` |
| `CONS-H02-AC5` | audit release | tag annotato locale/remoto `096f195` -> `68f3b90`; installer, SHA-256 `8CD723...DE92` e Build ID `8268f442-...` coincidono nell'annotazione pubblicata | `PASS` |
