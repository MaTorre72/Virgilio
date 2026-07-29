Avanza Virgilio di un solo task chiudibile in questa run di 30 minuti.

1. Leggi solo `AGENTS.md`, `docs/sviluppo/CODEX_STATE.md` e
   `docs/sviluppo/NEXT_CODEX_TASKS.md`.
2. Verifica branch `codex/v1.1-development` e working tree pulito; altrimenti fermati.
3. Esegui esclusivamente il task `CORRENTE` indicato in `NEXT_CODEX_TASKS.md`.
4. Prima di scrivere codice, individua e riusa le funzioni CLI, GAS e i test gia` citati dal task. Non reimplementare capacita` esistenti; correggi solo il collegamento o la regressione provata.
5. Implementa il minimo percorso verticale che chiude tutti i criteri. Niente UX, refactor, pulizie o documentazione estranei.
6. Esegui prima i test mirati; esegui lo smoke richiesto solo dopo il loro successo.
7. Aggiorna solo la scheda del task e i due puntatori operativi; massimo un commit atomico, working tree pulito.

Non usare servizi, mail, Google o credenziali reali. Non eseguire `clasp push`, deploy, reset remoto o gate umani senza autorizzazione esplicita. Se il task e` bloccato, registra una sola causa e una sola azione necessaria, poi fermati. Output finale: massimo 8 righe.
