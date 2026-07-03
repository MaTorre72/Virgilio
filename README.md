# Virgilio

Virgilio e' il progetto interno Sigma+ per guidare apertura pratiche, presa in carico allegati e tracciamento operativo.

## Stato v1.1 sperimentale

La v1.0 resta l'MVP Google Workspace mono-utente. La linea v1.1 consolida il lavoro sperimentale sul Local IMAP Connector e prepara un'architettura meno dipendente da Google Apps Script:

- **Virgilio**: interfaccia, guida e supervisione umana;
- **Caronte Locale**: motore operativo locale, multi-casella e provider-agnostico;
- **Apps Script**: adattatore Google opzionale, non nucleo definitivo;
- **SQLite locale**: registro operativo primario del connettore locale;
- **Bucoliche**: output adapter ispezionabile, non database primario;
- **Drive Desktop**: storage adapter iniziale di test, non architettura definitiva.

La branch `codex/v1.1-development` serve a consolidare componenti gia' testati. Non introduce nuove funzioni operative.

## Profili operativi

| Profilo | Quando usarlo | Superficie | Vincoli |
|---|---|---|---|
| Google-only | se il task tocca `apps_script/src`, `apps_script/clasp`, GmailApp o `clasp` | Apps Script e snapshot Google | resta nel perimetro Google Workspace |
| Local connector | se il task tocca `local_connector/src/virgilio_connector` o i test locali | motore locale, fixture e CLI | resta offline, senza servizi reali |

Se il task passa da Apps Script o dal progetto Google, il profilo attivo e` Google-only. Se passa dal motore locale o dai test, il profilo attivo e` Local connector.

## Stato architetturale

Virgilio ha due ingressi tecnici e un solo flusso operativo: Google-only e Local connector confluiscono entrambi in `Limbo -> Da archiviare -> Form -> Pratica finale -> Registro`. Nella UX la coda si chiama `Da archiviare`; `Virgilio_Inbox` resta il nome tecnico del tab. La sorgente canonica Apps Script vive in `apps_script/src`, lo snapshot `clasp` in `apps_script/clasp`, e il local connector resta separato, locale e testabile senza servizi reali.
Il riferimento condiviso per lessico e flusso e` [Architettura unificata](docs/ARCHITETTURA_UNIFICATA.md).

## Componenti

| Area | Percorso | Ruolo |
|---|---|---|
| Google-only sorgente | `apps_script/src/` | moduli Apps Script canonici |
| Google-only snapshot | `apps_script/clasp/` | mirror `clasp`, non sorgente |
| Local connector | `local_connector/src/virgilio_connector/` | motore locale, offline e testabile |
| Test local connector | `local_connector/tests/` | fixture e test automatici |
| Documentazione | `docs/` | riferimento condiviso e backlog |
| Documenti storici | `docs/archive/` | conservati per audit |

## Confini v1.1

In questa fase non sono abilitati come comportamento produttivo:

- ack IMAP automatico;
- upload reale generalizzato;
- spostamento messaggi;
- scrittura Bucoliche reale dal flusso locale senza fase controllata;
- notifiche operative;
- multi-account completo;
- AI.

## Test locali

```powershell
cd local_connector
.\.venv\Scripts\python.exe -m pytest
```

Se la virtualenv e' nella root del repository, usare:

```powershell
.\.venv\Scripts\python.exe -m pytest local_connector
```

I test del connettore non devono usare credenziali reali, Gmail reale, Drive reale o Bucoliche reale.

## Documentazione principale

- [Architettura](docs/ARCHITECTURE.md)
- [Architettura unificata](docs/ARCHITETTURA_UNIFICATA.md)
- [Caronte Locale](docs/LOCAL_CARONTE.md)
- [Setup e test](docs/SETUP_AND_TEST.md)
- [Roadmap v1.1](docs/ROADMAP_V1_1.md)
- [Decisioni](docs/DECISIONS.md)

## Principio operativo

**L'AI propone. Il tecnico valida. Il sistema registra.**

Ogni automazione critica deve restare verificabile, reversibile e tracciata.

## Sviluppo autonomo con Codex

Il ciclo autonomo e` governato da:

- `AGENTS.md`: regole permanenti e limiti operativi;
- `docs/DEV_BACKLOG.md`: ordine dei task e stato di avanzamento;
- `docs/DEFINITION_OF_DONE.md`: gate obbligatori;
- `docs/AUTONOMOUS_DEVELOPMENT.md`: protocollo di scelta, esecuzione e stop;
- `.github/codex/prompts/advance.md`: prompt per avanzare un task;
- `scripts/dev/smoke_local_connector.ps1`: suite, CLI e controllo segreti;
- `.github/workflows/local-connector-ci.yml`: verifica senza servizi reali.

Per il prossimo task autonomo usare il prompt `advance.md`, oppure chiedere "vai avanti".

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1
```

Comandi essenziali:

```powershell
virgilio init-config --output accounts.local.yaml --email nome@azienda.it --staging-dir C:\Virgilio\staging
python -m virgilio_connector doctor --config accounts.local.yaml --human
virgilio pilot --config accounts.local.yaml --human
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1
```

- `init-config` prepara il profilo locale.
- `doctor` controlla la configurazione.
- `pilot` mostra il flusso senza effetti operativi.
- Lo smoke locale resta la verifica finale minima.

Per un collaudo completo usa prima `--dry-run` e solo dopo un account di test:

```powershell
python -m virgilio_connector run-local-pipeline --config accounts.local.yaml --dry-run --human
python -m virgilio_connector pilot-run --config accounts.local.yaml --dry-run --human
python -m virgilio_connector pilot-run --config accounts.local.yaml --human
```

`--dry-run` significa test controllato. Il run senza `--dry-run` va usato solo su
configurazioni di test gia' verificate.
