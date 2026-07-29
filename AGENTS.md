# AGENTS.md - Virgilio

## Missione
Virgilio acquisisce documenti da email, li porta nel Limbo, li mette in Da archiviare,
raccoglie la decisione umana e li archivia nella pratica finale registrando tutto nel Registro.

Riferimento architetturale condiviso: `docs/tecnica/ARCHITETTURA.md`.

## Regole permanenti
- Non modificare `main`.
- Lavorare su `codex/v1.1-development` o su una branch derivata.
- Un task per run, al massimo un commit per task.
- Non usare mail, Google o credenziali reali nei test.
- Non inviare byte, base64 o path locali ad Apps Script.
- Non versionare segreti, token, password, `.env`, `.env.*`, `.local_data/`, `.secrets/`, `_staging/` o `.clasprc.json`.
- Non introdurre AI, RAG, Docling, LiteLLM, database remoti o server web.
- Non sono ammesse GUI parallele. Le sole presentazioni target sono
  `virgilio_connector.user_app` per `Caronte` e la nuova presentazione separata
  di `Caronte Manutenzione` esposta da `virgilio_connector.maintenance_gui`.
- L'implementazione GUI legacy (`gui`, `gui_*`) e` abbandonata: non deve essere
  sviluppata, distribuita o importata dalle nuove presentazioni. L'entry point
  `maintenance_gui` resta target, ma deve cessare di riesportare il legacy quando
  sara` implementata la nuova suite di manutenzione.
- Non riscrivere il form.
- Non sostituire Apps Script con Python.
- Non eseguire `clasp push` salvo task esplicito.
- Se il working tree e` sporco per cause non spiegate, fermarsi.
- Progettare la GUI utente a partire dalle attivita` dell'utente finale, non dall'elenco dei comandi CLI.
- Non trasformare automaticamente i comandi CLI in pulsanti: una corrispondenza uno-a-uno
  non costituisce una GUI utente completa.
- GUI utente, nuova GUI manutenzione e CLI devono condividere servizi
  applicativi, senza duplicare la logica operativa.
- Nella GUI utente non devono comparire termini o dettagli tecnici interni.
- La GUI puo` richiamare direttamente servizi interni quando un sottoprocesso CLI compromette UX,
  reattivita` o controllo del processo.
- Nessun task puo` restare aperto per rifiniture generiche o non misurabili.
- I gate umani non possono essere approvati autonomamente da Codex.

## Workflow
- Verificare branch e `git status --short` prima di modificare.
- Usare `docs/sviluppo/CODEX_STATE.md` e
  `docs/sviluppo/NEXT_CODEX_TASKS.md` come fonti operative primarie.
- Usare `docs/sviluppo/DEV_BACKLOG.md` solo per il task selezionato.
- Usare `docs/tecnica/ARCHITETTURA.md` solo per dubbi architetturali.
- Usare la sezione Apps Script di
  `docs/tecnica/OPERAZIONI_E_MANUTENZIONE.md` solo per task Apps Script o
  `clasp`.
- Tenere i cambi piccoli, reversibili e coerenti con il lessico ufficiale.

## Test
- Se si tocca codice, aggiungere test mirati prima dello smoke.
- Quando il task tocca il percorso locale o la governance di sviluppo, eseguire
  `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1`.
- Non usare servizi reali nei test.

## Chiusura run
- Verificare diff, stato git e assenza di segreti.
- Aggiornare `docs/sviluppo/CODEX_STATE.md`,
  `docs/sviluppo/NEXT_CODEX_TASKS.md` e, se necessario, solo la sezione
  pertinente di `docs/sviluppo/DEV_BACKLOG.md`.
- Verificare `docs/sviluppo/DEFINITION_OF_DONE.md` prima di chiudere il task.
- Committare solo quando il task e` completo.
- Non fare merge o reset distruttivi.
