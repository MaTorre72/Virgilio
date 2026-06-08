# Struttura del repository

## File Apps Script

I file Apps Script restano nella radice per mantenere semplice il collegamento con il progetto Google:

- `caronte.gs`: motore operativo, Drive, Limbo, Gmail v1.0, form backend.
- `bucoliche.gs`: registro Google Sheets.
- `notifiche.gs`: Google Chat e Telegram.
- `anagrafiche.gs`: tab anagrafiche e dropdown del form.
- `setup.gs`: trigger e configurazione PropertiesService.
- `test.gs`: test manuali Apps Script.
- `webapp.gs`: endpoint HTML service.
- `virgilio.html`: interfaccia del form.

## Documentazione

- `README.md`: descrizione funzionale e architetturale.
- `docs/GIT_WORKFLOW.md`: uso di Git, rami e versioni.
- `docs/REPO_STRUCTURE.md`: questa mappa.
- `VERSION`: versione stabile corrente.

## Asset

- `Virgilio.png`, `VirgilioBN.png`: asset correnti.
- `Virgilio_1.0.png`, `VirgilioBN_1.0.png`: asset congelati per v1.0.
- `*.svg`: diagrammi e materiali sorgente visuali.

## Esclusi da Git

La configurazione in `.gitignore` esclude:

- credenziali e token locali;
- `_old/` e archivi ZIP storici;
- PDF, DOCX e notebook generati;
- cache Python e ambienti virtuali;
- configurazioni locali di editor.

Questi file restano sul disco, ma non entrano nella storia Git.
