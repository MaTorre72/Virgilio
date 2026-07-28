# Mappa della documentazione

La documentazione corrente e` ridotta a 19 file Markdown. Per orientarsi bastano
tre ingressi:

1. `README.md` per prodotto, prerequisiti e limiti;
2. `docs/ARCHITETTURA_UNIFICATA.md` per struttura e confini;
3. `docs/RUNBOOKS.md` per setup, test, operazioni, Apps Script, build e pulizia.

## Documenti correnti

| Gruppo | File | Scopo |
| --- | --- | --- |
| Pubblico | `README.md`, `CHANGELOG.md` | uso e release |
| Tecnico | `docs/ARCHITETTURA_UNIFICATA.md`, `docs/RUNBOOKS.md` | architettura e procedure |
| Consegna | `docs/HANDOFF_1_1.md` | handoff verificabile della 1.1 |
| Governo | `AGENTS.md`, `docs/DEFINITION_OF_DONE.md` | regole permanenti e criteri di chiusura |
| Stato | `docs/CODEX_STATE.md`, `docs/NEXT_CODEX_TASKS.md`, `docs/DEV_BACKLOG.md` | puntatori operativi |
| Evidenze | `docs/CHANGELOG_DEV.md`, `docs/CONSOLIDATION_PROGRAM.md`, `docs/SURFACE_INVENTORY.md`, questo file | storia e audit del consolidamento |
| Test | `local_connector/tests/README.md` | livelli della suite |
| Prompt | quattro file in `.github/codex/prompts/` | ingressi Codex specializzati |

I 17 file di `docs/archive/`, quattro documenti architetturali duplicati e
cinque runbook specialistici sono stati rimossi dopo l'assorbimento nelle fonti
canoniche. Restano integralmente recuperabili dalla storia Git precedente alla
pulizia documentale.
