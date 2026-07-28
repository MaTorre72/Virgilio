# Next Codex Task

## CORRENTE - CONS-H01 - Onboarding da clone pulito

Stato: `TODO`. Priorita`: `P1`.

Risultato: una persona parte da un clone pulito, prepara l'ambiente locale e
raggiunge uno smoke verde seguendo un solo percorso breve e verificato.

Dipendenze: `CONS-C05` chiuso `DONE`; livelli e gate completo della suite sono
espliciti e ripetibili.

Componenti ammessi: guida di onboarding corrente, script di bootstrap/smoke,
configurazione di sviluppo e relativi puntatori.

Esclusioni: refactor applicativi, servizi reali, credenziali, deploy, modifica o
merge di `main`.

Condizione di blocco: il percorso non e` riproducibile in un ambiente isolato
senza credenziali o dipendenze non dichiarate, oppure upstream diverge.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-H01-AC1` prerequisiti e percorso unico sono brevi ed espliciti. | revisione guida |
| `CONS-H01-AC2` bootstrap installa tutte e sole le dipendenze dichiarate. | ambiente isolato |
| `CONS-H01-AC3` clone pulito raggiunge help e test senza dati reali. | prova fresh clone |
| `CONS-H01-AC4` lo smoke completo passa nell'ambiente appena creato. | smoke fresh clone |
| `CONS-H01-AC5` diff, segreti e puntatori sono verificati. | controlli Git |

## SUCCESSIVO

`CONS-H02` - audit finale di struttura, documenti, segreti, build e release.

## EVIDENZA CONS-C05

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| --- | --- | --- | --- |
| `CONS-C05-AC1` | inventario suite | inventario vincolante per modulo; nuovi, duplicati o riferimenti obsoleti bloccano la raccolta | `PASS` |
| `CONS-C05-AC2` | comandi mirati | `unit`: 171 passed; `contract`: 99 passed, con script unico parametrico | `PASS` |
| `CONS-C05-AC3` | esecuzione isolata | `integration_offline`: 276 passed con fake, fixture sintetiche e risorse locali | `PASS` |
| `CONS-C05-AC4` | smoke locale | gate completo esegue tutti i 546 test una sola volta e conserva i controlli esistenti | `PASS` |
| `CONS-C05-AC5` | confronto raccolta e controlli Git | 171 + 99 + 276 = 546; diff, segreti e puntatori verificati | `PASS` |
