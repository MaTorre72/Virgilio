# Sviluppo autonomo

## Ciclo

- Frequenza prevista per il consolidamento: ogni 60 minuti.
- Esecuzione seriale: un solo task e massimo un commit per run.
- Il task corrente deve chiudersi nella run; nessun secondo task viene iniziato.

## Contesto minimo

Leggere sempre e soltanto:

1. `AGENTS.md`;
2. `docs/CODEX_STATE.md`;
3. `docs/NEXT_CODEX_TASKS.md`.

Il task corrente indica i soli file di codice, test e riferimenti aggiuntivi da aprire. Consultare
`DEV_BACKLOG`, architettura, storico o workflow `clasp` solo se il task lo richiede espressamente.

Per il programma di consolidamento usare `docs/CONSOLIDATION_PROGRAM.md` solo
per individuare il successore immediato; la scheda completa corrente resta in
`docs/NEXT_CODEX_TASKS.md`.

## Sincronizzazione Git

- Prima del task: tree pulito, `git fetch origin --prune`, confronto di HEAD,
  upstream e merge-base; `git pull --ff-only` solo quando e` dimostrato sicuro.
- Dopo il task: commit atomico, nuovo fetch, push esplicito della branch corrente
  e verifica della coincidenza locale/remota.
- Divergenza, upstream inatteso o push rifiutato sono condizioni di stop.
- Vietati force-push, merge automatico e modifica diretta di `main`.

## Efficienza e budget

- Modello e reasoning dell'automazione: `gpt-5.6-sol`, `low`.
- Usare `rg` e letture circoscritte; non caricare backlog o storici completi.
- Test a scalare: mirati, area, smoke soltanto quando richiesto.
- Il consumo token settimanale non e` esposto alla run: non stimarlo. Riportare
  `token_usage=non_esposto`; se il dato diventa disponibile, sospendere dopo il
  90% del budget disponibile registrato all'avvio del programma.

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
