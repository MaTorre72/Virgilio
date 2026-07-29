# Installazione e ambiente di sviluppo

## Ambito

Questa procedura prepara un clone per leggere il codice, eseguire la suite
offline e costruire Caronte. Non configura automaticamente caselle o Google e
non autorizza effetti reali. Per i comandi operativi consulta il
[Riferimento comandi](RIFERIMENTO_COMANDI.md); per l'ambiente reale consulta
[Configurazione e integrazioni](CONFIGURAZIONE_E_INTEGRAZIONI.md).

## Prerequisiti

| Componente | Requisito | Note |
| --- | --- | --- |
| Sistema | Windows 11 x64 | target collaudato per GUI, credenziali e installer |
| Git | versione corrente supportata | necessario per clone, branch e controlli |
| Python | 3.11 o successivo | per build serve una distribuzione completa con Tcl/Tk |
| PowerShell | Windows PowerShell 5.1 o PowerShell compatibile | gli script usano `-NoProfile` |
| Drive Desktop | installato solo per uso operativo | non serve ai test offline |
| Node / clasp | soltanto per task Apps Script | non richiesto al connettore locale |
| Inno Setup / strumenti build | soltanto per installer | verificati dallo script di build |

Il package Python dichiara in `local_connector/pyproject.toml`:

- runtime: `google-auth`, `google-auth-oauthlib`, `requests`, `tzdata`;
- extra `dev`: pytest;
- extra `build`: PyInstaller.

Non esiste un secondo `requirements.txt` canonico. Aggiungere una dipendenza
significa aggiornare `pyproject.toml`, il lock/processo previsto e i test
pertinenti.

## Clone e orientamento

```powershell
git clone https://github.com/MaTorre72/Virgilio.git Virgilio
cd Virgilio
git status --short
git branch --show-current
```

`main` contiene la release ufficiale 1.1.0 e va trattata come sola lettura. Il
workflow del repository richiede `codex/v1.1-development` o una branch derivata
per le modifiche. Prima di cambiare branch verificare sempre che il working
tree sia pulito. Per un task ordinario creare una branch derivata con prefisso
`codex/`; la pipeline dell'installer di accettazione e` piu` restrittiva e
accetta esattamente `codex/v1.1-development`, non una derivata. Il release
manager deve quindi preparare quella branch sul commit approvato prima del
build, senza spostare tag esistenti.

La struttura essenziale e`:

```text
apps_script/src/                         sorgente canonica Google
local_connector/src/virgilio_connector/ package Python
local_connector/tests/                   suite offline
scripts/dev/                             bootstrap, smoke e build
docs/utente/                             manuale d'uso
docs/tecnica/                            riferimento del sistema
docs/sviluppo/                           governance e storia dello sviluppo
icone/                                   unico catalogo delle icone
```

## Bootstrap automatico

Da radice repository:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/bootstrap_local_connector.ps1
```

Lo script:

1. individua il runtime Python richiesto;
2. crea `local_connector/.venv`;
3. aggiorna gli strumenti di packaging previsti;
4. installa il package in editable mode con l'extra `dev`;
5. non crea configurazioni, credenziali o connessioni reali.

Per scegliere esplicitamente Python:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/bootstrap_local_connector.ps1 -Python C:\Percorso\python.exe
```

Se un antivirus o un ACL impedisce la creazione dell'ambiente, non cambiare i
permessi dell'intero repository. Verificare il percorso preciso e usare una
cartella di lavoro consentita.

## Verifica immediata

```powershell
local_connector\.venv\Scripts\python.exe -m virgilio_connector --help
local_connector\.venv\Scripts\python.exe -c "import virgilio_connector; print(virgilio_connector.__version__)"
```

Il primo comando deve elencare i subcommand senza richiedere rete. Il secondo
deve stampare `1.1.0` sulla release ufficiale.

## Configurazione sintetica per sviluppo

Il repository contiene:

- `local_connector/accounts.example.yaml`;
- `local_connector/.env.example`.

Copie locali reali non vanno committate. Per generare una configurazione
innocua:

```powershell
local_connector\.venv\Scripts\python.exe -m virgilio_connector init-config `
  --output local_connector\accounts.local.yaml `
  --email test@example.invalid `
  --staging-dir C:\Virgilio\Limbo-Test
```

Il dominio `.invalid` non e` instradabile. Non sostituirlo con un account reale
per eseguire i test.

## Test a scalare

### Test mirato

```powershell
local_connector\.venv\Scripts\python.exe -m pytest `
  local_connector\tests\test_<area>.py -q
```

### Livelli dichiarati

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts/dev/test_local_connector_level.ps1 -Level unit

powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts/dev/test_local_connector_level.ps1 -Level contract

powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts/dev/test_local_connector_level.ps1 -Level integration_offline
```

### Smoke completo

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1
```

Lo smoke controlla governance, file vietati, segreti, import, sintassi e suite
offline. Non deve contattare servizi reali. Se fallisce per una directory
`.pytest-tmp-*` bloccata, chiudere i processi che possiedono handle e rimuovere
soltanto la directory temporanea verificata; non cancellare `.local_data` o
configurazioni operative.

## Build Caronte

La build non e` un normale test di sviluppo. Richiede tree e versione compresi,
extra `build`, runtime con Tcl/Tk e asset da `icone/`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/build_caronte.ps1
```

Per produrre l'installer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/build_caronte_installer.ps1
```

Gli output vivono sotto `local_connector/build-output/` e sono rigenerabili.
Prima di pubblicare verificare:

- versione del package;
- commit sorgente;
- Build ID;
- manifest build;
- nome e SHA-256 dell'installer;
- smoke dell'eseguibile e dell'installer;
- assenza di credenziali e configurazioni locali.

La distribuzione pubblica si costruisce senza client OAuth incorporato. Per
Gmail Workspace e Registro Google l'amministratore fornisce dopo
l'installazione un proprio client Desktop esterno tramite
`CARONTE_GOOGLE_OAUTH_CLIENT_PATH`, come descritto in
[Configurazione e integrazioni](CONFIGURAZIONE_E_INTEGRAZIONI.md). Il parametro
di build resta disponibile per distribuzioni controllate autorizzate; il JSON
non va mai copiato nel repository o negli artefatti di supporto.

## Apps Script per sviluppatori

La sorgente da modificare e` `apps_script/src`; non mantenere uno snapshot
parallelo. `clasp status`, `clasp pull`, `clasp push` e deploy appartengono a un
task Apps Script esplicito. Un clone preparato per i test locali non deve avere
bisogno di login Google.

Prima di qualunque sincronizzazione reale verificare progetto, branch, tree e
diff; non stampare token e non versionare `.clasp.json` o `.clasprc.json`.
Procedure e gate sono in
[Operazioni e manutenzione](OPERAZIONI_E_MANUTENZIONE.md).

## File rigenerabili e file da proteggere

| Rigenerabili | Da proteggere / sottoporre a backup |
| --- | --- |
| `.pytest_cache`, `.pytest-tmp*`, `__pycache__` | `.local_data/` operativo |
| ambienti virtuali | `state.db` |
| `local_connector/build-output/` | configurazione YAML reale |
| `artifacts/`, `_staging/` di build | credenziali, token e client OAuth |

Il fatto che un percorso sia ignorato da Git non significa che sia eliminabile:
prima di pulire distinguere cache da stato operativo.

## Problemi comuni di setup

- **Python non trovato:** passare `-Python` con un percorso assoluto verificato.
- **Tkinter mancante:** usare una distribuzione Python completa prima della
  build GUI.
- **Import fallito:** eseguire il bootstrap dalla radice e usare il Python della
  venv, non un interprete globale.
- **ExecutionPolicy:** usare il comando documentato con `-ExecutionPolicy
  Bypass` solo per gli script versionati del repository.
- **Test che cercano servizi reali:** fermarsi; un test repository deve usare
  fake e fixture.
- **Tree sporco dopo lo smoke:** controllare se sono cache ignorate o modifiche
  tracciate; non usare reset distruttivi.
