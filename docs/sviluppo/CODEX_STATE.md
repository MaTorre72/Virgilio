# Codex State

- Release ufficiale: Virgilio `1.1.0` e` su `main`; la versione 1.0 resta nel
  tag storico `v1.0`.
- Baseline preservata: commit funzionale `7e18277`, collaudo umano `PASS` del
  2026-07-28 e Apps Script deployment `40`.
- Pubblicazione: la pull request `#1` da `codex/v1.1-development` e` stata unita
  su `main` con revisione umana; merge commit `77730b3`.
- Distribuzione GitHub: la [Release `v1.1.0`](https://github.com/MaTorre72/Virgilio/releases/tag/v1.1.0)
  pubblica il build Windows `20260729` dal commit `68f3b90`, SHA-256
  `A6C87E6748ACC8C72970353B4686F219B28412D444847E7E436C818FB07DDB11`,
  Build ID `254daca5-af1d-4951-85dd-f1119a3f0437`; installer, manifest e
  checksum riscaricati coincidono con gli originali locali. Il client OAuth non
  e` incorporato e viene predisposto esternamente dall'amministratore.
- Programma `CONS`: completato. Non esistono task CONS correnti e l'automazione
  di consolidamento deve restare in pausa.
- Branch di sviluppo attesa per nuovi task: `codex/v1.1-development` o una
  derivata, mai modifica diretta di `main`.
- Documentazione corrente: ingresso unico `docs/README.md`, con sezioni
  `docs/utente/`, `docs/tecnica/` e `docs/sviluppo/`.
- Documentazione storica: recuperabile dalla cronologia Git; nessuna cartella
  `docs/archive` e nessun puntatore compatibile al livello principale.
- Riordino documentale: pull request `#2` unita su `main` con commit di squash
  `a17419c`; la branch documentale locale e remota e` stata rimossa.
- CI repository: il workflow GitHub Actions disabilitato `local-connector-ci`
  e` stato rimosso. Il gate completo resta lo smoke locale
  `scripts/dev/smoke_local_connector.ps1`.
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
