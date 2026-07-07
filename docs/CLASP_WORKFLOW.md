# Workflow clasp

## Ambito

Questo workflow vale solo per il profilo Google-only, cioe` per il progetto Apps Script in `apps_script/src`.
Se il task tocca `local_connector`, non usare `clasp` e resta nel flusso locale.

## Prerequisiti

- Node.js installato in locale.
- npm disponibile.
- `clasp` installato e accessibile da shell.

## Controllo minimo

Per capire subito se il profilo Google-only e pronto:

```powershell
node -v
clasp --version
git branch --show-current
git status --short
clasp status
```

Se `clasp` manca:

```powershell
npm install -g @google/clasp
```

## Login iniziale

- Verificare che `clasp` sia autenticato prima di lavorare su Apps Script.
- Se non e` loggato, fermarsi e chiedere all'utente di eseguire `clasp login`.
- Non usare workaround manuali con credenziali.
- Non stampare token.

Comando:

```powershell
clasp login
```

## Collegamento del progetto

- Identificare la cartella Apps Script nel repository.
- La sorgente canonica vive in `apps_script/src`.
- `appsscript.json` vive in `apps_script/src`.
- `.clasp.json` vive nella root del repo e punta a `apps_script/src`.
- Non esiste una cartella mirror separata.
- Se manca `.clasp.json`, prima ottenere lo `scriptId` dal progetto reale e poi crearla alla root del repo.
- Non creare `.clasp.json` senza autorizzazione esplicita quando serve salvare il collegamento.
- Non committare `.clasprc.json`.

Comandi essenziali:

```powershell
clasp pull
clasp status
```

## Prima di ogni `clasp pull`

- Controllare branch e `git status --short`.
- Verificare di essere sul progetto reale.
- Evitare pull se il working tree contiene cambi locali non compresi.
- Se necessario, annotare il diff atteso prima di sincronizzare.

## Prima di ogni modifica Apps Script

- Eseguire `clasp pull`.
- Creare una branch dedicata.
- Esaminare il diff locale prima di editare.
- Non sovrascrivere codice live senza confronto.

## Sequenza setup Caronte

Per le attivita` su `apps_script/src` usare sempre questa sequenza manuale, distinta dal flusso di produzione (`doPost()` / `caronteTraghetta()`):

1. Impostare le Script Properties con `caronteSetupCredenziali(...)`.
2. Verificare i segreti con `caronteStatoCredenziali()`.
3. Verificare la configurazione con `caronteStatoConfigurazione()`.
4. Creare il trigger con `caronteSetupTrigger()`.
5. Controllare lo stato con `caronteStatoTrigger()`.
6. Mettere in pausa con `caronteStopTrigger()` quando serve.
7. Eseguire il test minimo con `caronteTest()`; usare `caronteTestFinale()` solo per un collaudo completo.

## Prima di ogni `clasp push`

- Mostrare file modificati.
- Mostrare diff sintetico.
- Valutare il rischio.
- Ottenere conferma esplicita o avere un task che richieda il push.

`clasp push` richiede conferma esplicita o task dedicato.

Comando:

```powershell
clasp push
```

## Procedura per non sovrascrivere codice Apps Script live

- Lavorare sempre sul progetto reale collegato.
- Fare `clasp pull` prima di editare.
- Tenere una branch dedicata per la modifica.
- Limitare i cambi a file mirati.
- Riesaminare il diff prima del push.
- Se il live e` cambiato, fermarsi e riconciliare.

## Checklist pre-push

- `clasp status` coerente.
- Branch corretta.
- Diff compreso.
- Nessun segreto toccato.
- Nessun file di credenziali nel commit.
- Niente modifiche non volute sul progetto live.
- Conferma esplicita presente.

## Regola finale

`clasp push` non si esegue di default. Si esegue solo quando il task lo prevede o quando l'utente lo chiede chiaramente.
