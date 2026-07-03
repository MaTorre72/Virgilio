# Workflow clasp

## Ambito

Questo workflow vale solo per il profilo Google-only, cioe` per `apps_script/src` e `apps_script/clasp`.
Se il task tocca `local_connector`, non usare `clasp` e resta nel flusso locale.

## Prerequisiti

- Node.js installato in locale.
- npm disponibile.
- `clasp` installato e accessibile da shell.

Verifiche iniziali:

```powershell
node -v
npm -v
clasp --version
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
- La snapshot gestita da `clasp` vive in `apps_script/clasp`.
- Verificare se esiste `.clasp.json`.
- Se manca `.clasp.json`, prima ottenere lo `scriptId` dal progetto reale e poi collegare la cartella.
- Non creare `.clasp.json` senza autorizzazione esplicita quando serve salvare il collegamento.
- Non committare `.clasprc.json`.

Comandi utili:

```powershell
clasp clone <SCRIPT_ID> apps_script
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
