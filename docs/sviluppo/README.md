# Documentazione per lo sviluppo

Questa cartella contiene tutto cio` che serve a sviluppatori, manutentori e
automazioni. Non e` documentazione per l'uso quotidiano e non va citata come
prerequisito per l'utente finale.

## Inizio rapido per un nuovo sviluppatore

1. Leggi [`AGENTS.md`](../../AGENTS.md): vincoli permanenti e workflow.
2. Comprendi l'[architettura](../tecnica/ARCHITETTURA.md) e il
   [modello dati](../tecnica/MODELLO_DATI_E_STATI.md).
3. Prepara l'ambiente con
   [Installazione e comandi](../tecnica/INSTALLAZIONE_E_COMANDI.md).
4. Segui [Come contribuire](CONTRIBUIRE.md).
5. Prima di iniziare un task, leggi `CODEX_STATE.md` e
   `NEXT_CODEX_TASKS.md`.

## Roadmap e decisioni

| Documento | Uso |
| --- | --- |
| [ROADMAP_1_1.md](ROADMAP_1_1.md) | roadmap originale A-H, stato raggiunto e direzioni successive |
| [DECISIONI_E_RISCHI.md](DECISIONI_E_RISCHI.md) | decisioni consolidate, temi aperti e rischi da rivalutare |
| [CONTRIBUIRE.md](CONTRIBUIRE.md) | workflow, test, struttura dei task e review |

## Documenti operativi Codex

| Documento | Autorita` | Quando leggerlo |
| --- | --- | --- |
| `CODEX_STATE.md` | fotografia corrente di branch, baseline e programma | all'inizio di una run |
| `NEXT_CODEX_TASKS.md` | unico task Codex corrente e criteri binari | prima di modificare |
| `DEV_BACKLOG.md` | dettagli del solo programma/task selezionato | se richiamato dal task |
| `DEFINITION_OF_DONE.md` | gate di chiusura comuni | prima del commit |
| `CHANGELOG_DEV.md` | cronologia tecnica dettagliata | ricerca storica mirata |

Questi documenti sono intenzionalmente separati dalla documentazione tecnica:
descrivono come e` stato governato lo sviluppo, non il funzionamento del
prodotto.

## Consolidamento e handoff 1.1

| Documento | Contenuto |
| --- | --- |
| `CONSOLIDATION_PROGRAM.md` | programma seriale CONS che ha chiuso la 1.1 |
| `HANDOFF_1_1.md` | release, prove, limiti e consegna verso main |
| `DOCUMENT_INVENTORY.md` | classificazione delle fonti correnti |
| `SURFACE_INVENTORY.md` | audit di entry point, package, script e asset |

Sono evidenze storiche ancora utili per audit. Nuovi sviluppi non devono
riaprire CONS: devono creare un programma e criteri nuovi.

## Cronologia e recuperabilita`

Non esiste una sottocartella `archive`. La cronologia Git conserva documenti,
report e piani rimossi; quando serve una prova storica si usa il commit o il tag
che la conteneva. Questo evita che fonti superate appaiano valide accanto alla
documentazione corrente.

Riferimenti di rilascio:

- `v1.0`: versione storica Google-only;
- `v1.1.0`: release ufficiale corrente;
- commit funzionale collaudato `7e18277`;
- collaudo umano `PASS` del 28 luglio 2026;
- deployment Apps Script `40`.
