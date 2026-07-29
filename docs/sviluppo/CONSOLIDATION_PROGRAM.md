# Programma di consolidamento Virgilio 1.1

## Obiettivo finito

Pubblicare Virgilio `1.1.0`, ridurre il repository alla sola versione corrente
con `v1.0` conservata tramite tag, rendere documentazione e codice consegnabili a
nuovi sviluppatori e preparare una pull request verso `main` senza modificare o
unire autonomamente `main`.

Baseline funzionale: commit `7e18277`, RC `0.11.0-7e18277`, collaudo umano
finale `PASS` del 2026-07-28, Apps Script deployment `40`, smoke `599 passed`.

## Regole del programma

- Un task per run, massimo un commit e nessun lavoro fuori dai criteri correnti.
- Nessuna nuova funzione: rilascio, semplificazione e refactor devono preservare
  il comportamento collaudato.
- Mai force-push, merge automatico, modifica diretta di `main`, `clasp push`,
  deploy, servizi reali o cancellazioni remote non espressamente previste.
- Ogni rimozione richiede prova di non raggiungibilita`, test mirato e recupero
  possibile dal tag o dalla storia Git.
- I task di codice usano fixture sintetiche e test mirati prima dello smoke.
- Se il tree e` sporco, la branch diverge o un criterio non e` chiudibile nella
  run, registrare un solo blocco e fermarsi con tree pulito.

## Protocollo Git autonomo

All'inizio di ogni run:

1. verificare branch e `git status --short`;
2. eseguire `git fetch origin --prune`;
3. confrontare `HEAD`, upstream e merge-base;
4. usare `git pull --ff-only` soltanto se il remoto e` avanti e il locale ne e`
   antenato; fermarsi in caso di divergenza;
5. non cambiare branch durante un task ordinario.

Alla chiusura:

1. eseguire prove, diff e scansione segreti richiesti;
2. aggiornare task e puntatori operativi;
3. creare un commit atomico;
4. rifare `git fetch origin` e verificare che l'upstream non sia avanzato;
5. eseguire push esplicito di `HEAD` sulla branch corrente, mai `--force`;
6. verificare che commit locale e remoto coincidano.

## Budget e monitoraggio

La piattaforma corrente non espone alle automazioni il residuo settimanale o i
token consumati. Il programma applica quindi un limite operativo del 90% come
riserva logica, senza inventare conteggi:

- modello `gpt-5.6-sol`, reasoning `low`;
- una run ogni 60 minuti e nessuna run parallela;
- lettura iniziale limitata ad `AGENTS.md`, `CODEX_STATE.md` e
  `NEXT_CODEX_TASKS.md`;
- apertura della sola scheda corrente e dei file indispensabili;
- `rg` e letture mirate invece di riversare file lunghi nel contesto;
- test mirati, poi test di area, smoke soltanto ai gate previsti;
- output massimo 10 righe;
- riportare `token_usage=non_esposto` finche` la piattaforma non fornisce un dato
  verificabile; se un contatore diventa disponibile, registrare valore e residuo
  e sospendere al raggiungimento del 90% del budget disponibile alla partenza.

## Coda seriale

| Ordine | Task | Risultato verificabile | Gate principale |
| --- | --- | --- | --- |
| 1 | `CONS-R01` | versione prodotto unica `1.1.0`; `0.11.0` resta identificata come RC storica | test versione/build |
| 2 | `CONS-R02` | README e changelog descrivono la 1.1 ufficiale e i limiti reali | link e coerenza |
| 3 | `CONS-R03` | build release, installer, manifest e checksum prodotti dal commit candidato | smoke build/installer |
| 4 | `CONS-R04` | tag annotato `v1.1.0` e relativi riferimenti remoti verificati | nessun tag preesistente/conflitto |
| 5 | `CONS-D01` | inventario documentale `KEEP/MERGE/HISTORY/REMOVE` completo | ogni file classificato |
| 6 | `CONS-D02` | architettura corrente unificata in un solo documento canonico | nessuna contraddizione nota |
| 7 | `CONS-D03` | setup, sviluppo, test, operazioni e release hanno runbook brevi | comandi verificati |
| 8 | `CONS-D04` | backlog/report storici condensati nella storia 1.1 e rimossi dal percorso corrente | link verdi, Git recuperabile |
| 9 | `CONS-G01` | inventario entry point, comandi, import e file inclusi nella build | mappa di raggiungibilita` |
| 10 | `CONS-G02` | GUI legacy `gui`/`gui_*` e test esclusivi rimossi senza impatto sui target | test GUI/build |
| 11 | `CONS-G03` | spike AI/LiteLLM/Docling e superfici sperimentali non supportate rimossi | import/CLI/test verdi |
| 12 | `CONS-G04` | asset e script storici non necessari rimossi o spostati nelle release | inventario e link verdi |
| 13 | `CONS-C01` | `__init__.py` espone solo API intenzionali e una sola fonte versione | import contract |
| 14 | `CONS-C02` | comandi CLI classificati supportati/interni/rimossi | snapshot help |
| 15 | `CONS-C03` | parser e dispatch CLI separati dal bootstrap `__main__` | test comando per gruppo |
| 16 | `CONS-C04` | primo modulo operativo monolitico separato per responsabilita` | test caratterizzazione |
| 17 | `CONS-C05` | test organizzati per unita`, contratti, integrazione offline e smoke | CI completa |
| 18 | `CONS-H01` | guida di onboarding e prova da clone pulito ripetibile | fresh-clone smoke |
| 19 | `CONS-H02` | audit finale di struttura, documenti, segreti, build e release | tutti i gate verdi |
| 20 | `CONS-H03` | branch pubblicata e pull request verso `main` pronta per revisione umana | nessun merge automatico |

## Specifica del task corrente

`docs/sviluppo/NEXT_CODEX_TASKS.md` contiene sempre la scheda completa del solo task
corrente: risultato, massimo cinque criteri binari, prove, dipendenze, componenti
ammessi, esclusioni e condizione di blocco. Alla chiusura la run copia dal
programma soltanto il successore immediato e non apre un secondo task.

## Condizione di completamento

Il programma e` completo quando `v1.1.0` e` pubblicata, la pull request verso
`main` e` pronta, il repository corrente non contiene copie della 1.0 fuori
dalla storia/tag, la suite offline e le build sono verdi e un nuovo sviluppatore
puo` installare, testare, costruire e localizzare i principali casi d'uso usando
soltanto la documentazione canonica.
