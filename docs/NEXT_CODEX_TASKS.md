# Next Codex Task

## CORRENTE - CONS-D04 - Storia 1.1 condensata

Stato: `TODO`. Priorita`: `P1`.

Risultato: backlog e report chiusi confluiscono in una storia 1.1 concisa; i
documenti storici non compaiono nel percorso operativo corrente.

Dipendenze: `CONS-D03` chiuso `DONE`; runbook correnti canonici.

Componenti ammessi: documenti `HISTORY`, inventario, changelog e soli link
necessari a separare storia e percorso corrente.

Esclusioni: modifica funzionale, servizi reali, build/deploy, modifica o merge
di `main`; nessuna rimozione senza prova di link e recuperabilita` Git.

Condizione di blocco: documento storico ancora necessario come fonte corrente,
link non riconciliabile o upstream divergente.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-D04-AC1` la storia 1.1 chiusa e` condensata senza perdere esiti e baseline. | confronto changelog e inventario |
| `CONS-D04-AC2` backlog e report storici non sono fonti operative correnti. | ricerca link e intestazioni |
| `CONS-D04-AC3` ogni rimozione prevista e` non raggiungibile e recuperabile da Git. | `rg`, `git log` e test link |
| `CONS-D04-AC4` README, runbook e puntatori rimandano solo a fonti correnti. | verifica link mirata |
| `CONS-D04-AC5` diff, segreti e puntatori sono verificati. | controlli Git e documentali |

## SUCCESSIVO

`CONS-G01` - inventario di entry point, comandi, import e file inclusi nella build.
