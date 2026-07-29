# Configurazione e integrazioni

Questa guida descrive dove vive la configurazione di Virgilio 1.1, quali dati
sono strutturali, dove devono restare i segreti e come si collegano Caronte,
IMAP, il Limbo sincronizzato, Apps Script, il Registro e le notifiche.

Per il disegno complessivo usa [ARCHITETTURA.md](ARCHITETTURA.md); per avvio,
diagnostica e ripristino usa
[OPERAZIONI_E_MANUTENZIONE.md](OPERAZIONI_E_MANUTENZIONE.md). Gli esempi qui
sotto sono sintetici: non copiare identificativi, indirizzi o credenziali reali
nel repository.

## Mappa delle fonti autorevoli

| Informazione | Fonte in una installazione Caronte | Deve entrare in Git? |
| --- | --- | --- |
| caselle, cartelle IMAP, Limbo e preferenze | `%APPDATA%\Caronte\config.yaml` | no |
| password IMAP, token OAuth e chiave Virgilio | Gestione credenziali Windows, prefisso `Caronte/` | mai |
| stato, quarantena, log, report ed export locali | `%LOCALAPPDATA%\Caronte` | no |
| ID Drive/Sheets, endpoint e notifier cloud | Script Properties del progetto Apps Script | mai |
| codice e manifest Apps Script | `apps_script/src` | sì, senza valori operativi |
| icone distribuite con il progetto | `icone/` | sì |
| variabili per esecuzioni da checkout | ambiente del processo o `.env` locale ignorato | no |

`config.yaml` contiene riferimenti e preferenze, non segreti. Le presentazioni
`Caronte`, `Caronte Manutenzione` e la CLI consumano gli stessi servizi di
configurazione; non mantenere copie divergenti per ciascuna interfaccia.

## Percorsi Windows

I percorsi predefiniti non dipendono dalla directory dalla quale si avvia il
programma:

| Contenuto | Percorso predefinito |
| --- | --- |
| configurazione | `%APPDATA%\Caronte\config.yaml` |
| dati locali | `%LOCALAPPDATA%\Caronte` |
| database | `%LOCALAPPDATA%\Caronte\state.db` |
| quarantena | `%LOCALAPPDATA%\Caronte\quarantine\{incoming,rejected,ready}` |
| log | `%LOCALAPPDATA%\Caronte\logs` |
| report diagnostici | `%LOCALAPPDATA%\Caronte\reports` |
| export tecnici | `%LOCALAPPDATA%\Caronte\exports` |

`VIRGILIO_CONFIG_DIR` e `VIRGILIO_LOCAL_DATA_DIR` consentono override assoluti
per collaudi isolati o ambienti amministrati. Non usarli per puntare al
repository e non condividere la stessa cartella dati fra più processi o più
postazioni. La disinstallazione rimuove programma e collegamenti, ma conserva
configurazione e dati dell'utente.

## Struttura di `config.yaml`

Il primo avvio guidato crea e aggiorna il file. Per sviluppo si può generare uno
scheletro con `init-config`; la sintassi accettata è intenzionalmente limitata e
non equivale a un parser YAML generico.

Esempio sintetico completo:

```yaml
accounts:
  - account_alias: casella_amministrativa
    email: ufficio@example.invalid
    provider_hint: generic_imap
    imap_host: imap.example.invalid
    imap_port: 993
    username_env: VIRGILIO_CASELLA_AMMINISTRATIVA_USERNAME
    password_env: VIRGILIO_CASELLA_AMMINISTRATIVA_PASSWORD
    input_folder: INBOX
    done_folder: done
    error_folder: error
    enabled: true
    max_messages: 25
    ack_enabled: false
    ack_strategy: no_ack_manual

storage:
  adapter: local_filesystem
  staging_dir: "C:\\Dati\\Google Drive\\Virgilio\\Limbo"
  use_account_subfolders: false
  copy_manifest: true
  overwrite: false
  create_staging_dir: false

preferences:
  interval_seconds: 300
  start_with_windows: false
  minimize_on_close: false

bucoliche:
  enabled: true
  adapter: google_sheets_append_only
  spreadsheet_id: "ID_SINTETICO_DEL_REGISTRO"
  events_sheet: bucoliche
  credentials_mode: user_oauth_local
  append_only: true
  dry_run_default: true

virgilio_connection:
  endpoint_url: "https://script.google.com/macros/s/ID_SINTETICO/exec"

rules:
  default_action: include
```

Le sezioni hanno responsabilità diverse:

- `accounts` descrive una o più caselle; `account_alias` deve essere univoco,
  stabile, minuscolo e sicuro per un nome di cartella;
- `storage` identifica la copia locale del Limbo sincronizzato da Google Drive
  per desktop; il percorso deve essere assoluto ed esistente;
- `preferences` governa frequenza del controllo, avvio con Windows e chiusura;
- `bucoliche` identifica il Registro condiviso e il suo adapter append-only;
- `virgilio_connection` conserva soltanto l'endpoint HTTPS `/exec`; la chiave
  associata resta nel deposito protetto;
- `rules` decide quali messaggi o allegati includere, senza modificare la
  mailbox.

### Caselle IMAP

Per `gmail_workspace` i valori iniziali sono `imap.gmail.com:993` e le cartelle
`Virgilio/da-traghettare`, `Virgilio/traghettate`, `Virgilio/errore`. Caronte
usa il consenso OAuth Desktop, autentica IMAP con XOAUTH2 e conserva il token
nel deposito protetto Windows. Il client OAuth Desktop è predisposto da chi
costruisce la distribuzione; l'utente non deve scegliere un file JSON.

Per un server `generic_imap` l'amministratore deve confermare host, porta e
nomi effettivi delle cartelle. La password o password applicativa resta nel
deposito protetto. La porta deve essere compresa fra 1 e 65535; il flusso
ordinario usa IMAP TLS sulla porta 993.

`username_env` e `password_env` sono nomi stabili usati come riferimenti. Nella
distribuzione installata corrispondono a credenziali generiche Windows con
target `Caronte/<nome-riferimento>`; non implicano che il segreto sia scritto
nel file YAML. Nel percorso CLI da checkout gli stessi nomi possono essere
valorizzati nell'ambiente del processo.

`max_messages` limita il lavoro per ciclo. Al primo avvio mantenere
`ack_enabled: false` e `ack_strategy: no_ack_manual`: scansione e acquisizione
restano read-only verso la casella. Le strategie `add_done_label_only` e
`move_to_done_label` introducono una scrittura IMAP dopo i gate di
completamento; vanno abilitate solo con un collaudo amministrativo dedicato.

### Limbo e storage

`storage.adapter` deve rimanere `local_filesystem`. `staging_dir` è la cartella
locale sincronizzata che rappresenta lo stesso Limbo configurato in Apps
Script con `VIRGILIO_LIMBO_ID`.

Vincoli della 1.1:

- `copy_manifest` deve restare `true`: documento e manifest JSON viaggiano in
  coppia;
- `overwrite` deve restare `false`: un nome già occupato non viene sostituito;
- `create_staging_dir` è normalmente `false`: l'utente seleziona una cartella
  esistente e già sincronizzata;
- `use_account_subfolders` è facoltativo, ma va concordato con la topologia del
  Limbo e con le verifiche cloud.

Caronte copia nel Limbo i file già ammessi dalla policy e verificati dallo
scanner locale. Al servizio Apps Script invia esclusivamente metadati e
identificativi Drive; non invia byte, base64 o path locali. La sincronizzazione
Drive è asincrona: un file può essere presente localmente ma non ancora
visibile all'adapter cloud, condizione che produce attesa e retry, non una
seconda copia.

### Preferenze

`interval_seconds` deve essere compreso fra 60 e 86400. Il valore predefinito è
300 secondi. `start_with_windows` e `minimize_on_close` sono preferenze utente;
non sostituiscono la configurazione del task di controllo automatico.

### Regole di inclusione

Il comportamento iniziale è `default_action: include`. Per profili più
restrittivi si possono dichiarare regole deterministiche:

```yaml
rules:
  default_action: exclude
  include:
    - name: documenti_pdf
      subject_contains: ["pratica", "istanza"]
      filename_extensions: [".pdf", ".p7m"]
      require_attachment: true
  exclude:
    - name: notifiche_automatiche
      from_contains: ["noreply"]
```

Una regola può usare `subject_contains`, `from_contains`,
`filename_contains`, `filename_extensions`, `min_attachment_size_bytes`,
`max_attachment_size_bytes` e `require_attachment`. Viene applicata la prima
regola corrispondente; in assenza di corrispondenze vale `default_action`.
Testare sempre le regole con fixture sintetiche prima di applicarle a una
casella operativa.

## Segreti e ambiente CLI

Il comando `python -m virgilio_connector` carica, se presente nella directory
corrente, un file `.env`. È una comodità di sviluppo, non la configurazione
canonica dell'app installata. Il file deve restare ignorato e non va allegato a
issue, report o commit. `.env.example` documenta solo nomi e valori neutri.

Variabili correnti del connettore locale:

| Variabile | Uso |
| --- | --- |
| i nomi dichiarati in `username_env` / `password_env` | credenziali IMAP del processo CLI |
| `VIRGILIO_CONFIG_DIR` | override della directory configurazione |
| `VIRGILIO_LOCAL_DATA_DIR` | override della directory dati |
| `VIRGILIO_MAX_ATTACHMENT_BYTES` | limite allegato, predefinito 25 MiB |
| `VIRGILIO_SCANNER` | `auto`, `windows_defender` o `none`; `clamav` non è implementato |
| `VIRGILIO_CARONTE_TIMEOUT_SECONDS` | timeout HTTP, predefinito 15 secondi |
| `VIRGILIO_CARONTE_DRIVE_VERIFY_URL` | endpoint di verifica visibilità Drive |
| `VIRGILIO_CARONTE_INTAKE_URL` | endpoint operativo di Da archiviare |
| `VIRGILIO_TOKEN` | token dell'endpoint nel solo ambiente del processo |

Le seguenti variabili servono a comandi tecnici o percorsi controllati, non
alla normale configurazione della GUI:

- `VIRGILIO_LOCAL_DRIVE_STAGING_ENABLED` e
  `VIRGILIO_LIMBO_LOCAL_SYNC_DIR` alimentano il wrapper tecnico
  `stage-ready-files`;
- `VIRGILIO_CARONTE_DRY_RUN_URL` alimenta il bridge metadata-only;
- `VIRGILIO_CARONTE_INTAKE_TEST_URL` alimenta l'intake esclusivamente TEST;
- `VIRGILIO_BUCOLICHE_SPREADSHEET_ID`,
  `VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON`,
  `VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH` e
  `VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH` appartengono al percorso CLI storico per
  Google Sheets. La GUI installata usa invece il Registro scelto nel YAML e il
  token OAuth protetto in Gestione credenziali Windows;
- `CARONTE_GOOGLE_OAUTH_CLIENT_PATH` indica, durante build o sviluppo
  controllato, il client OAuth Desktop fornito dall'amministratore. Il file
  deve chiamarsi `google_oauth_client.json` e restare fuori dal repository.

Non stampare il contenuto delle variabili sensibili. Nei report indicare solo
`configurata`, `mancante` o il nome simbolico della variabile.

## Integrazione Apps Script

Apps Script è l'adapter canonico per form Virgilio, Drive, Da archiviare,
archiviazione finale e Registro. Il codice vive in `apps_script/src`; i valori
operativi vivono nelle Script Properties del progetto distribuito.

### Proprietà operative

| Script Property | Funzione | Sensibile |
| --- | --- | --- |
| `VIRGILIO_BUCOLICHE_SPREADSHEET_ID` | workbook del Registro/Bucoliche | identificativo operativo |
| `VIRGILIO_INBOX_SPREADSHEET_ID` | workbook che contiene Da archiviare | identificativo operativo |
| `VIRGILIO_INBOX_SHEET_NAME` | tab tecnico, predefinito `Virgilio_Inbox` | no |
| `VIRGILIO_EMPIREO_ID` | radice Drive delle pratiche | identificativo operativo |
| `VIRGILIO_ADAMO_ID` | cartella modello per nuove pratiche | identificativo operativo |
| `VIRGILIO_LIMBO_ID` | cartella Drive del Limbo | identificativo operativo |
| `VIRGILIO_TOKEN` | autenticazione delle azioni POST operative | sì |
| `WEBHOOK_CHAT` | webhook Google Chat | sì |
| `TELEGRAM_TOKEN` | token del bot Telegram | sì |
| `TELEGRAM_CHAT_ID` | destinatario Telegram | dato operativo |
| `URL_FORM` | URL `/exec` del form distribuito | no, ma dipende dal deployment |

`VIRGILIO_ENVIRONMENT=TEST` è richiesto soltanto dal reset remoto coordinato e
non va impostato in produzione. `VIRGILIO_INTAKE_TEST_SPREADSHEET_ID` e
`VIRGILIO_INTAKE_TEST_SHEET_NAME` appartengono esclusivamente all'intake di
prova controllato.

Usare `caronteStatoConfigurazione()` e `caronteStatoCredenziali()` per vedere
quali valori mancano: le funzioni riportano presenza e lunghezza, non il
contenuto. `generaToken()` produce il token di collegamento; il medesimo valore
va salvato nelle Script Properties e, tramite Caronte Manutenzione, nel deposito
protetto della postazione.

`caronteSetupVirgilioInbox(spreadsheetId, sheetName)` crea o consolida il solo
tab Da archiviare e registra gli identificativi. Non usare funzioni TEST per
preparare asset di produzione.

### Collegamento Caronte -> Apps Script

Caronte Manutenzione richiede due valori:

1. l'URL HTTPS del deployment Apps Script che termina con `/exec`;
2. la chiave uguale a `VIRGILIO_TOKEN` nelle Script Properties.

L'URL viene scritto nella sezione `virgilio_connection`; la chiave viene
salvata in Gestione credenziali Windows. A runtime il servizio espone questi
valori ai soli adapter che verificano Drive, creano il record Da archiviare e
ne leggono lo stato finale.

Il contratto è metadata-only. Il manifest identifica account, messaggio,
allegato, nome sanificato, SHA-256, dimensione e stato di scansione. Gli ID
Drive vengono aggiunti soltanto dopo che il file e il manifest risultano
visibili nella cartella cloud corretta.

### Registro/Bucoliche

Il Registro scelto dall'amministratore è una Google Sheet identificata da ID
stabile; spostare il file in un'altra cartella Drive non richiede
riconfigurazione. La 1.1 usa l'adapter `google_sheets_append_only` e il tab
canonico `bucoliche`: gli eventi vengono aggiunti, non riscritti per correggere
la storia.

La GUI usa OAuth utente e conserva l'autorizzazione con riferimento protetto
`Caronte/VIRGILIO_BUCOLICHE_GOOGLE_OAUTH`. Il percorso CLI supporta anche un
service account passato per variabile ambiente, ma non va incorporato nel
repository né confuso con il flusso utente installato.

### Notifiche

La disponibilità di un documento può essere notificata tramite Google Chat,
Telegram o entrambi. L'URL del form collegato al record Da archiviare viene
inserito nel messaggio; i dettagli tecnici come `inbox_id` non vengono mostrati
all'utente.

- senza canali configurati, il record resta valido con stato notifica
  `not_configured`;
- se un canale fallisce, lo stato è `retry` e l'errore viene registrato;
- dopo `sent`, il retry idempotente non invia un duplicato;
- un errore di notifica non deve duplicare la presa in carico.

La rotazione di webhook o token si esegue nelle Script Properties. Non
inserire mai questi valori in `notifiche.gs`, nei log o nelle schermate.

### Icone

La sola raccolta grafica versionata è `icone/`. Non aggiungere copie dei PNG in
root o in cartelle documentali. Il form Apps Script carica l'icona da Drive
tramite `VIRGILIO_ICON_FILE_ID` dichiarato in `apps_script/src/webapp.gs`; il
file Drive deve derivare dall'asset approvato in `icone/`. Un cambio dell'ID è
una modifica di codice Apps Script e richiede il normale controllo di diff e
deployment, non una Script Property improvvisata.

## Checklist di configurazione

Prima di dichiarare pronta una postazione:

1. `config.yaml` esiste nel percorso corretto ed è leggibile dalle due GUI;
2. almeno una casella è abilitata e le sue credenziali protette sono presenti;
3. il Limbo locale esiste, è scrivibile ed è sincronizzato con la cartella
   Drive indicata da `VIRGILIO_LIMBO_ID`;
4. Registro, Da archiviare, Empireo e Adamo puntano agli asset attesi;
5. endpoint `/exec` e token coincidono fra postazione e Script Properties;
6. il consenso Google richiesto è stato completato dall'account autorizzato;
7. i notifier desiderati risultano configurati senza esporne i valori;
8. `doctor` e il controllo integrità non riportano blocchi;
9. il primo ciclo viene eseguito in modalità controllata prima di abilitare
   ack IMAP o avvio automatico.
