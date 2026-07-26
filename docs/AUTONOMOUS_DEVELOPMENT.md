# Sviluppo autonomo

## Ciclo

- Frequenza prevista: ogni 30 minuti.
- Esecuzione seriale: un solo task e massimo un commit per run.
- Il task corrente deve chiudersi nella run; nessun secondo task viene iniziato.

## Contesto minimo

Leggere sempre e soltanto:

1. `AGENTS.md`;
2. `docs/CODEX_STATE.md`;
3. `docs/NEXT_CODEX_TASKS.md`.

Il task corrente indica i soli file di codice, test e riferimenti aggiuntivi da aprire. Consultare
`DEV_BACKLOG`, architettura, storico o workflow `clasp` solo se il task lo richiede espressamente.

## Regola di sviluppo

Virgilio possiede gia` CLI, servizi applicativi e GAS funzionanti. Prima di aggiungere codice:

1. cercare l'implementazione esistente citata dal task;
2. riprodurre la regressione con fixture o fake;
3. correggere il minimo punto di composizione o invariante;
4. preservare contratti, idempotenza e test gia` verdi.

Sono vietati reimplementazioni parallele, refactor preventivi, polishing e micro-task estetici.

## Verifica e chiusura

- Test mirati prima dello smoke.
- Smoke locale solo quando richiesto da `AGENTS.md` o dal task.
- Nessun servizio reale nei test.
- Aggiornare soltanto scheda corrente, `CODEX_STATE.md` e `NEXT_CODEX_TASKS.md`.
- Se serve autorita` umana (`clasp push`, deploy, reset remoto, collaudo), fermarsi al gate.
- Output finale massimo 8 righe: risultato, test, commit oppure singolo blocco.

Toolchain: `local_connector\.venv\Scripts\python.exe`; lo smoke e`
`scripts\dev\smoke_local_connector.ps1`.
