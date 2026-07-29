# Codex State

- Release ufficiale: Virgilio `1.1.0` e` su `main`; la versione 1.0 resta nel
  tag storico `v1.0`.
- Baseline preservata: commit funzionale `7e18277`, collaudo umano `PASS` del
  2026-07-28 e Apps Script deployment `40`.
- Pubblicazione: la pull request `#1` da `codex/v1.1-development` e` stata unita
  su `main` con revisione umana; merge commit `77730b3`.
- Programma `CONS`: completato. Non esistono task CONS correnti e l'automazione
  di consolidamento deve restare in pausa.
- Branch di sviluppo attesa per nuovi task: `codex/v1.1-development` o una
  derivata, mai modifica diretta di `main`.
- Documentazione corrente: ingresso unico `docs/README.md`, con sezioni
  `docs/utente/`, `docs/tecnica/` e `docs/sviluppo/`.
- Documentazione storica: recuperabile dalla cronologia Git; nessuna cartella
  `docs/archive` e nessun puntatore compatibile al livello principale.
- Riordino documentale: branch `docs/roadmap-architettura-modulare`, pull
  request `#2` verso `main`; nessun cambiamento al comportamento applicativo.
- Fonti operative per una futura run: `AGENTS.md`, questo file e
  `docs/sviluppo/NEXT_CODEX_TASKS.md`.

## Stato funzionale da non reinterpretare

Virgilio ha due ingressi tecnici e un solo flusso operativo. Il profilo
Google-only e il Local connector condividono Limbo, Da archiviare, form, pratica
finale e Registro. SQLite resta stato tecnico locale; Bucoliche resta audit
umano append-only.

## Task corrente

Nessuno. Un nuovo programma deve essere autorizzato e descritto con risultato,
massimo cinque criteri binari, prove, componenti ammessi, esclusioni e
condizione di blocco. Non riaprire automaticamente CONS.
