# Inventario delle fonti documentali

## Struttura corrente

L'ingresso unico e` [`docs/README.md`](../README.md). Al suo stesso livello non
esistono manuali, backlog o runbook: ogni fonte appartiene a una sola area.

### Utente

| Fonte | Scopo |
| --- | --- |
| `utente/README.md` | indice per chi usa Virgilio |
| `utente/MANUALE.md` | panoramica completa, ruoli e flusso |
| `utente/PRIMO_AVVIO.md` | configurazione guidata |
| `utente/USO_QUOTIDIANO.md` | procedura ordinaria |
| `utente/RISOLUZIONE_PROBLEMI.md` | messaggi, azioni sicure ed escalation |

### Tecnica

| Fonte | Scopo |
| --- | --- |
| `tecnica/README.md` | indice amministratori/sviluppatori |
| `tecnica/ARCHITETTURA.md` | componenti, profili, flusso e invarianti |
| `tecnica/MODELLO_DATI_E_STATI.md` | identita`, persistenza, code e audit |
| `tecnica/INSTALLAZIONE_E_COMANDI.md` | ambiente e setup ripetibile |
| `tecnica/CONFIGURAZIONE_E_INTEGRAZIONI.md` | confini e configurazione degli adapter |
| `tecnica/OPERAZIONI_E_MANUTENZIONE.md` | diagnosi, backup, reset e release |
| `tecnica/RIFERIMENTO_COMANDI.md` | CLI e script disponibili |
| `tecnica/SICUREZZA_E_TEST.md` | minacce, controlli e strategia di test |

### Sviluppo

| Gruppo | Fonti |
| --- | --- |
| orientamento | `README.md`, `CONTRIBUIRE.md` |
| direzione | `ROADMAP_1_1.md`, `DECISIONI_E_RISCHI.md` |
| stato e task | `CODEX_STATE.md`, `NEXT_CODEX_TASKS.md`, `DEV_BACKLOG.md` |
| governance | `DEFINITION_OF_DONE.md`, `CONSOLIDATION_PROGRAM.md` |
| evidenze | `HANDOFF_1_1.md`, `SURFACE_INVENTORY.md`, `CHANGELOG_DEV.md` |
| inventario | questo documento |

Il changelog pubblico delle versioni resta [`CHANGELOG.md`](../../CHANGELOG.md).
`AGENTS.md` e `.github/codex/prompts/` sono regole/ingressi repository e puntano
esplicitamente ai documenti di questa area.

## Fonti rimosse dal percorso corrente

La cartella `docs/archive` e i documenti duplicati precedenti non sono fonti
correnti. Restano recuperabili per commit e tag Git. In particolare, la roadmap
originale e le decisioni che hanno portato alla linea local-first sono state
aggiornate e assorbite in `ROADMAP_1_1.md`, `DECISIONI_E_RISCHI.md` e nella
documentazione tecnica; non sono state copiate in un secondo archivio.

## Regola di manutenzione

Un nuovo documento deve avere pubblico, proprietario logico e collegamento
dall'indice della sua area. Se duplica una fonte esistente, si aggiorna la fonte
canonica e si usa Git per conservare la versione precedente.
