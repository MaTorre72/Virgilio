# Operazioni e manutenzione

Questa guida è destinata a chi amministra una postazione Caronte, prepara una
release o interviene su un malfunzionamento. Distingue le operazioni ordinarie
dalle azioni che modificano stato, servizi Google o installazione.

Per chi usa quotidianamente Virgilio resta autorevole il manuale in
`docs/utente`; per chi configura integrazioni e segreti usa
[CONFIGURAZIONE_E_INTEGRAZIONI.md](CONFIGURAZIONE_E_INTEGRAZIONI.md). Il
riferimento completo della CLI è
[RIFERIMENTO_COMANDI.md](RIFERIMENTO_COMANDI.md).

## Responsabilità operative

| Ruolo | Attività |
| --- | --- |
| utente | controllare documenti, leggere gli esiti, compilare il form e decidere la pratica |
| amministratore Caronte | configurare caselle, Limbo, Registro, endpoint, avvio automatico, backup e diagnostica |
| amministratore Google | governare Drive, Sheets, Apps Script, deployment, autorizzazioni e notifier |
| sviluppatore/release manager | test offline, build, manifest, installer, commit, tag e pubblicazione |

L'utente non deve ricevere password, token, ID tecnici o comandi CLI. Le
operazioni amministrative si eseguono da **Caronte Manutenzione**; la CLI serve
a sviluppo, automazione controllata e diagnosi avanzata.

## Controllo quotidiano

Una postazione sana presenta questi segnali:

1. Caronte apre la Home senza chiedere di ripetere il primo avvio;
2. Registro e collegamento Virgilio risultano disponibili;
3. il controllo singolo termina con un esito leggibile;
4. i documenti ammessi avanzano da acquisizione a Limbo e Da archiviare;
5. i documenti in attesa di sincronizzazione non vengono duplicati;
6. Attività e problemi non mostrano errori persistenti o conflitti;
7. il controllo automatico, se abilitato, risulta attivo una sola volta.

Un ciclo senza nuovi documenti è un esito normale. Non riavviare ripetutamente
il processo e non spostare a mano file fra quarantena, Limbo e pratica per
forzare l'avanzamento.

## Diagnostica progressiva

Procedere dal controllo meno invasivo a quello più specifico.

### 1. Identità della build

Dalla finestra **Informazioni su Caronte** annotare versione, commit, data build
e Build ID. Su una distribuzione è disponibile anche:

```powershell
$caronteExe = "$env:LOCALAPPDATA\Programs\Caronte\Caronte.exe"
& $caronteExe --build-info
```

Usare il percorso realmente installato. Non sostituire un eseguibile a mano se
identità e manifest non coincidono.

### 2. Configurazione e collegamenti

In **Caronte Manutenzione** verificare:

- indirizzo del Registro condiviso;
- endpoint Apps Script HTTPS terminante in `/exec`;
- presenza della chiave protetta;
- integrità dell'archivio locale.

Dal checkout, per una diagnosi tecnica esplicita:

```powershell
$env:PYTHONPATH = (Resolve-Path "local_connector\src").Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector doctor `
  --config C:\percorso\config.yaml --human
```

`doctor` valida la struttura, inizializza/verifica SQLite, controlla la
scrivibilità del Limbo e, se trova credenziali, apre la casella in sola lettura.
Non è quindi un test offline puro. Usare soltanto account e servizi autorizzati.

### 3. Stato locale

La directory dati contiene:

| Elemento | Significato |
| --- | --- |
| `state.db` | stato transazionale, identità, eventi, retry e completamenti |
| `machine_id` | identità stabile della postazione |
| `quarantine/incoming` | allegati in elaborazione locale |
| `quarantine/ready` | allegati ammessi e pronti per il Limbo |
| `quarantine/rejected` | allegati rifiutati o non ammessi |
| `logs` | log locali quando prodotti dal processo |
| `reports` | report diagnostici redatti |
| `exports` | esportazioni tecniche JSONL/CSV |

Non aprire `state.db` in scrittura con strumenti esterni e non cancellare righe
per correggere un esito. Una modifica manuale spezza idempotenza e tracciabilità.

### 4. Report diagnostico

**Caronte Manutenzione -> Crea report diagnostico** scrive un JSON in
`reports`. Il servizio oscura automaticamente chiavi che contengono
`password`, `secret`, `token` o `credential`.

Prima di condividere il report:

1. aprirlo localmente;
2. verificare che non contenga indirizzi, percorsi o identificativi non
   necessari;
3. allegare versione, commit e orario del problema;
4. non allegare `config.yaml`, `.env`, `state.db` o file della quarantena.

La redazione automatica riduce il rischio, ma non sostituisce il controllo
umano del contenuto.

## Backup locale

### Backup ordinario

Chiudere o mettere in pausa il controllo, poi usare **Caronte Manutenzione ->
Crea backup**. Il servizio copia l'intera directory dati in una directory
sorella nominata:

```text
Caronte.backup-AAAAMMGG-HHMMSS-xxxxxxxx
```

La risposta indica percorso e numero di file copiati. Configurazione e segreti
non sono compresi, perché vivono rispettivamente in `%APPDATA%` e Gestione
credenziali Windows.

Per una copia destinata a conservazione:

- verificare che il controllo sia fermo;
- controllare presenza e dimensione di `state.db`, `machine_id` e quarantena;
- conservare data, versione applicativa e motivo del backup;
- proteggere il supporto con le stesse regole dei documenti acquisiti;
- non inserire il backup nel repository o in un ticket.

Il backup ordinario conta i file ma non calcola un hash completo. Il backup
automatico che precede il reset, invece, confronta dimensione e SHA-256 di ogni
file e annulla il reset se la verifica non coincide.

### Politica di conservazione

I backup non vengono rimossi automaticamente. Definire una retention locale
in base alle regole dell'organizzazione. Prima di eliminare un backup provare
che:

1. non è l'unica copia precedente a un reset;
2. una copia più recente è leggibile;
3. il problema per cui era stato creato è chiuso;
4. il percorso appartiene davvero alla directory dati della postazione.

## Verifica integrità

**Caronte Manutenzione -> Verifica integrità** esegue il controllo SQLite sul
solo `state.db`:

- `valid`: il database è leggibile e integro;
- `missing`: l'archivio non è ancora stato creato;
- `corrupt`: il controllo non è valido.

Con esito `corrupt`:

1. fermare Caronte e il controllo automatico;
2. creare o preservare una copia della directory dati senza modificarla;
3. annotare build e report diagnostico;
4. non eseguire cicli operativi né editing SQLite;
5. valutare il ripristino da backup con uno sviluppatore.

Non esiste nella 1.1 un pulsante di ripristino generico. Il ripristino è una
procedura amministrativa esplicita: si conserva prima lo stato corrente, si
seleziona un backup verificato, si ripristina a processo fermo e si valida
l'integrità prima di riattivare Caronte.

## Reset locale protetto

Il reset elimina lo stato operativo locale e la quarantena, ma preserva
configurazione, credenziali e identità della macchina. Non corregge problemi
nel Registro, in Drive o nella casella.

Percorso consigliato:

1. fermare il controllo automatico;
2. chiudere eventuali altre istanze di Caronte;
3. creare un report e verificare integrità;
4. in **Caronte Manutenzione** selezionare
   **Confermo il reset con backup automatico**;
5. premere **Esegui reset** una sola volta;
6. conservare il percorso del backup restituito;
7. eseguire un controllo singolo prima di riattivare l'automazione.

Equivalente CLI, destinato a un amministratore consapevole:

```powershell
$env:PYTHONPATH = (Resolve-Path "local_connector\src").Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector `
  reset-local-state --backup --confirm --human
```

Entrambi i flag sono obbligatori. Il comando acquisisce il lock operativo,
copia e verifica tutti i file, ricrea il layout, inizializza un nuovo
`state.db` e ripristina `machine_id` se esisteva. Se Caronte è ancora attivo,
il reset viene bloccato.

Il reset non deve diventare una risposta automatica a un errore: cancella
informazioni utili alla diagnosi e può rendere necessario riesaminare documenti
già acquisiti.

## Reset coordinato di un ambiente TEST

Esiste un protocollo separato che coordina stato locale, Registro TEST, Da
archiviare TEST e Limbo TEST. Non è una funzione di produzione.

Le protezioni richiedono:

- `VIRGILIO_ENVIRONMENT=TEST` nelle Script Properties;
- nomi degli asset contenenti esplicitamente `TEST`;
- ID validi e topologia coerente;
- un `reset_id` stabile;
- tre fasi `preview`, `prepare`, `execute`;
- backup remoto del Registro e del Limbo prima della cancellazione;
- conferma esplicita lato locale.

`preview` ispeziona, `prepare` crea i backup, `execute` svuota soltanto righe e
file TEST preservando schema e anagrafiche canoniche. Non impostare mai
artificialmente `TEST` su asset di produzione e non usare questo protocollo per
fare pulizia ordinaria.

## Conflitti e duplicati

Il fingerprint globale consente di riconoscere lo stesso allegato tra cicli e
postazioni. I conflitti non vengono risolti automaticamente.

Dal checkout:

```powershell
$env:PYTHONPATH = (Resolve-Path "local_connector\src").Path
local_connector\.venv\Scripts\python.exe -m virgilio_connector `
  check-local-conflicts --config C:\percorso\config.yaml
```

Possibili esiti:

- `OK`: nessun conflitto o duplicato osservato;
- `WARNINGS`: duplicati con stesso SHA-256;
- `CONFLICTS`: stesso riferimento con hash incompatibile, collisione di nome o
  manifest, oppure esiti cross-machine incompatibili.

Con `CONFLICTS` fermare l'ack, conservare gli eventi delle postazioni coinvolte
e scegliere manualmente una sola fonte autorevole. Non modificare a mano i tab
Bucoliche, non cancellare audit locali e non far convergere gli stati scrivendo
direttamente su SQLite.

## Controllo automatico Windows

La distribuzione installata registra un task per utente che avvia
`Caronte.exe watch` all'accesso Windows, con finestra nascosta e privilegi
limitati. La GUI ordinaria governa attivazione e disattivazione tramite i
servizi applicativi condivisi.

Per una diagnosi da checkout:

```powershell
local_connector\.venv\Scripts\python.exe -m virgilio_connector `
  status-windows-task --task-name "Virgilio Local Watch" --human
```

Prima di installare un task dal checkout usare sempre `--dry-run`; il piano
deve mostrare path assoluti del file di configurazione, del Python e del
repository. Non lasciare contemporaneamente il task della distribuzione e un
task di sviluppo sulla stessa configurazione.

La rimozione richiede `uninstall-windows-task --confirm`. Verificare il nome
esatto: un nome diverso non identifica lo stesso task.

## Matrice dei problemi comuni

| Sintomo | Controllo | Azione sicura |
| --- | --- | --- |
| configurazione richiesta a ogni avvio | percorso `%APPDATA%` e permessi | ripristinare il file corretto; non crearne copie nel programma |
| casella non collegata | credenziale protetta, host, porta e cartella ingresso | correggere in Manutenzione e ripetere la verifica read-only |
| scanner non disponibile | `VIRGILIO_SCANNER`, Microsoft Defender | ripristinare Defender; non dichiarare pulito un file `unverified` |
| documento fermo prima del Limbo | quarantena, policy, dimensione e scanner | leggere Attività/report; non spostare il file a mano |
| documento nel Limbo ma non in Da archiviare | sincronizzazione Drive e verifica cloud | attendere sync, verificare ID Limbo, poi un solo retry |
| endpoint rifiuta la richiesta | URL `/exec` e corrispondenza `VIRGILIO_TOKEN` | riallineare con Manutenzione; non stampare il token |
| Da archiviare non configurato | proprietà Inbox e presenza tab | eseguire setup esplicito del tab con l'amministratore Google |
| notifica `retry` | webhook Chat o credenziali Telegram | correggere il canale; non ricreare il record |
| Registro non disponibile | ID foglio, consenso OAuth, permessi | riautorizzare l'account corretto; non usare un foglio alternativo silenzioso |
| `operation busy` | altra GUI, worker o task attivo | fermare l'altra istanza e ripetere, senza forzare il lock |
| integrità non valida | `state.db` e backup | fermare tutto, preservare evidenze, pianificare ripristino |
| conflitto cross-machine | eventi e fingerprint delle postazioni | triage manuale e una fonte autorevole |

## Pulizia delle directory locali di sviluppo

Gli artefatti seguenti sono rigenerabili e non appartengono ai dati operativi:

- `.pytest-tmp-*`, `.pytest-tmp` e `.pytest_cache` dopo la fine dei test;
- `local_connector/build-output` dopo aver conservato gli artefatti release
  necessari;
- `__pycache__` e file `.pyc`;
- ambienti `.venv` soltanto se si accetta di reinstallare le dipendenze.

Non confonderli con `.local_data`, `%LOCALAPPDATA%\Caronte`, backup
`Caronte.backup-*`, configurazioni, manifest di release o dati sincronizzati
del Limbo.

Prima di rimuovere directory pytest chiudere processi Python e verificare che i
target siano figli della radice del checkout. Esempio PowerShell confinato:

```powershell
$repoRoot = (Resolve-Path ".").Path
$temporaryTests = Get-ChildItem -LiteralPath $repoRoot -Directory `
  -Filter ".pytest-tmp-*" -Force
$temporaryTests | Select-Object FullName

foreach ($temporaryTest in $temporaryTests) {
  $resolvedTarget = $temporaryTest.FullName
  if (-not $resolvedTarget.StartsWith(
      $repoRoot + [IO.Path]::DirectorySeparatorChar,
      [StringComparison]::OrdinalIgnoreCase)) {
    throw "Target fuori dal checkout: $resolvedTarget"
  }
  Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
}
```

Se Windows risponde `Access denied`, individuare prima il processo che mantiene
il file aperto. Non cambiare proprietario o ACL di una directory non ancora
identificata con certezza.

## Build di Caronte

Prerequisiti:

- Windows 11 x64;
- Python 3.11 o successivo completo di Tcl/Tk;
- dipendenze `dev` e `build` da `local_connector/pyproject.toml`;
- branch release autorizzata e working tree pulito;
- nessun segreto nel repository.

Preparazione della toolchain:

```powershell
Push-Location local_connector
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,build]"
Pop-Location
```

Build autonoma one-folder:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\build_caronte.ps1
```

Lo script verifica Tcl/Tk, legge versione e commit, genera
`build_manifest.json` e produce
`local_connector\build-output\dist\Caronte\Caronte.exe`. Una build di
collaudo umano usa `-HumanAcceptanceBuild` ed è accettata soltanto dalla branch
`codex/v1.1-development` con tree pulito.

Verifica della build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\smoke_caronte_build.ps1 `
  -BuildDirectory local_connector\build-output\dist\Caronte `
  -ExpectedBuildManifest local_connector\build-output\metadata\build_manifest.json
```

Lo smoke copia la distribuzione in una directory temporanea, rimuove i
riferimenti al checkout, confronta identità, verifica il worker e apre la
finestra Caronte.

## Installer e release desktop

La pipeline installer ricostruisce sempre la build e rifiuta un tree sporco o
una branch diversa da `codex/v1.1-development`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\dev\build_caronte_installer.ps1
```

Produce:

```text
local_connector\build-output\installer\dist\
  CaronteSetup-<versione>-<short-sha>.exe
  CaronteSetup-<versione>-<short-sha>.manifest.json
```

Il manifest release contiene dimensione, SHA-256, versione, commit, branch,
data UTC, Build ID e risultato degli smoke. Prima della pubblicazione verificare
che tutti questi valori coincidano con l'eseguibile installato.

Lo smoke installer crea radici isolate, installa per l'utente corrente, verifica
i due collegamenti **Caronte** e **Caronte Manutenzione**, confronta build info,
avvia entrambe le finestre, disinstalla e prova che configurazione e dati siano
conservati.

Il client OAuth Desktop opzionale si passa alla build con
`-GoogleOAuthClientPath` da un percorso protetto e deve chiamarsi
`google_oauth_client.json`. Non va mai copiato nel repository o negli artefatti
di supporto. La sua inclusione è registrata nel manifest senza esporne il
contenuto.

Checklist release:

1. versione unica coerente fra `_version.py`, package e tag previsto;
2. branch e commit identificati, tree pulito;
3. test mirati e smoke locale verdi;
4. build e smoke build verdi;
5. installer e smoke installer verdi;
6. manifest e SHA-256 conservati insieme all'artefatto;
7. nessun `.env`, token, client secret, service account o dato locale incluso;
8. note di rilascio e istruzioni di rollback aggiornate;
9. pubblicazione e tag eseguiti solo dal responsabile autorizzato.

## Apps Script: controllo e deployment

La sorgente canonica è `apps_script/src`, incluso `appsscript.json`. Il file
locale `.clasp.json`, quando autorizzato, collega il checkout al progetto
corretto e resta fuori dal repository.

Controlli non mutanti:

```powershell
node --version
clasp --version
git branch --show-current
git status --short
clasp status
```

Prima di un'attività Apps Script:

1. verificare login e progetto collegato;
2. controllare branch e tree;
3. eseguire `clasp pull` soltanto con tree compreso;
4. confrontare il pull con il codice locale;
5. eseguire test puri con fake prima di qualunque servizio reale;
6. mostrare file e diff attesi;
7. ottenere autorizzazione esplicita per `clasp push` e deploy.

`clasp push` non è un test e non è parte dello smoke locale. Può sovrascrivere
il progetto live; non eseguirlo per “riallineare” uno stato non compreso.

Dopo un push autorizzato, il deployment web resta un'operazione distinta. In
Apps Script aggiornare la versione del deployment, conservare l'URL `/exec`,
verificare le Script Properties senza stamparne i valori e controllare che
`Caronte Manutenzione` punti allo stesso endpoint. Il deployment esegue come
l'utente che distribuisce: permessi e ownership vanno verificati esplicitamente.

### Trigger e pausa

Funzioni amministrative disponibili nell'editor Apps Script:

| Funzione | Effetto |
| --- | --- |
| `caronteStatoConfigurazione()` | mostra presenza dei valori operativi senza segreti |
| `caronteStatoCredenziali()` | mostra presenza delle credenziali senza valori |
| `caronteSetupTrigger()` | elimina duplicati e crea un trigger `caronteTraghetta` ogni 5 minuti |
| `caronteStatoTrigger()` | elenca lo stato dei trigger Caronte |
| `caronteStopTrigger()` | rimuove i trigger `caronteTraghetta` e mette in pausa il profilo Google-only |

Creare il trigger soltanto dopo il collaudo previsto. Prima di manutenzione su
Drive, Sheets o configurazione, mettere in pausa e verificare che non restino
esecuzioni attive.

## Handoff di una postazione

Per consegnare il sistema a un altro amministratore, fornire separatamente:

- installer e relativo manifest/SHA-256;
- manuale utente e questa guida tecnica;
- inventario degli asset Google per nome e responsabile, senza segreti;
- procedura aziendale per concedere accesso a Registro, Limbo, Empireo e Adamo;
- posizione e retention dei backup;
- canale per la rotazione di token e notifier;
- versione, commit, deployment Apps Script e data dell'ultimo collaudo;
- problemi noti e ultimo report diagnostico già controllato.

Non trasferire credenziali esportandole in chiaro. Il nuovo amministratore deve
ricevere accessi tramite i sistemi ufficiali e completare i consensi con il
proprio account.
