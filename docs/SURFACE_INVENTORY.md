# Inventario delle superfici raggiungibili

Stato verificato per `CONS-G01` il 2026-07-28 e riallineato da `CONS-G04` dopo
la pulizia degli asset e degli script storici. L'inventario descrive la
raggiungibilita` statica della release 1.1.0.

## Ingressi

| Ingresso | Configurazione | Dispatch | Classificazione |
| --- | --- | --- | --- |
| `virgilio` | `[project.scripts]` in `local_connector/pyproject.toml` | `virgilio_connector.__main__:main` | CLI installata supportata |
| `python -m virgilio_connector` | `virgilio_connector/__main__.py` | `main()` | ingresso di sviluppo equivalente |
| `Caronte.exe` senza argomenti | `build/Caronte.spec` | `build_entry.main` -> `user_app.launch_user_app` | GUI utente supportata |
| `Caronte.exe maintenance-gui` | inoltro di `build_entry.main` al parser | `maintenance_gui.launch_gui` | GUI manutenzione supportata |
| `Caronte.exe --build-info` / `--smoke-about-available` / `--demo...` | dispatch riservato in `build_entry.py` | build info, smoke Informazioni, demo isolata | strumenti build/test interni |
| `CaronteSetup-*.exe` | `installer/CaronteSetup.spec` | `installer/caronte_installer.py` | installer e disinstaller supportati |

Il collegamento Start `Caronte` avvia l'eseguibile senza argomenti; il
collegamento `Caronte Manutenzione` lo avvia con `maintenance-gui`. La GUI
utente genera lo stesso comando tramite `maintenance_launch_command`.

## Comandi CLI e dispatch

La CLI installata mostra soltanto i tre comandi supportati destinati a uso
diretto. I comandi interni restano nel parser per gli ingressi applicativi, i
test offline e le procedure di manutenzione che li invocano esplicitamente;
non costituiscono interfaccia pubblica e non compaiono nell'help principale.

| Classificazione | Comandi | Motivazione |
| --- | --- | --- |
| supportato | `init-config`, `doctor`, `watch` | bootstrap, diagnosi e ciclo locale sono le azioni stabili della CLI tecnica |
| interno - pipeline | `scan-imap-accounts`, `process-imap-accounts`, `stage-ready-attachments`, `complete-staged-messages`, `ack-completed-messages`, `run-local-pipeline`, `check-local-conflicts` | stadi granulari coperti dai test e composti dai servizi applicativi |
| interno - integrazione | `send-caronte-dry-run`, `stage-ready-files`, `verify-drive-staging`, `intake-drive-staging-test`, `intake-da-archiviare` | adapter e probe controllati, non workflow utente autonomi |
| interno - Registro | `export-central-events`, `export-registro-events`, `export-to-bucoliche`, `refresh-bucoliche-state`, `doctor-bucoliche` | operazioni tecniche del Registro richiamate da manutenzione e prove offline |
| interno - collaudo | `pilot-check`, `pilot-run-safe`, `pilot-run`, `pilot`, `pilot-preview`, `setup-bucoliche-test-sheet` | orchestrazione e predisposizione della baseline collaudata |
| interno - piattaforma | `google-oauth-login`, `install-windows-task`, `status-windows-task`, `uninstall-windows-task`, `reset-local-state` | setup e manutenzione esposti dalle presentazioni tramite servizi condivisi |
| interno - ingresso | `user-gui`, `maintenance-gui` | target necessari a eseguibile, collegamenti Start e test di packaging |
| rimosso | `local-watch` | alias di sviluppo ridondante, senza consumer corrente; `watch` preserva lo stesso comportamento |

Ogni comando conservato ha un parser e un ramo esplicito in `__main__.main`.
L'alias rimosso resta recuperabile dalla storia Git precedente a `CONS-C02`.

## Import diretti dei target supportati

- `Caronte.exe` importa sempre `build_info`; il percorso normale importa
  `user_app`, mentre gli argomenti CLI importano `__main__`.
- `user_app.app` importa i servizi applicativi per account, attivita`,
  configurazione, stato/controllo Home, OAuth, operazioni, Registro, impostazioni,
  avvio Windows e credenziali; importa inoltre le sole viste sotto `user_app`.
- `maintenance_gui` importa i servizi applicativi `maintenance`, `credentials`,
  `operational_connection`, `registry_configuration` e `application_paths`.
- Nessuno dei due target GUI importa moduli della presentazione legacy rimossa
  in `CONS-G02`; gli ingressi supportati usano soltanto `user_app` e
  `maintenance_gui`.
- Il package root `virgilio_connector.__init__` espone intenzionalmente soltanto
  `__version__`: e` metadata stabile del prodotto e proviene dalla fonte unica
  `_version.py`. Classi, funzioni e costanti operative si importano dai moduli
  che le possiedono; gli ingressi supportati restano moduli importabili e non
  sono riesportazioni del root.

## Contenuto di package e build

| Artefatto | Inclusione verificata |
| --- | --- |
| wheel | package trovati sotto `local_connector/src`; metadata, dipendenze e `virgilio` definiti da `pyproject.toml`; nessun `package_data` esplicito |
| distribuzione `Caronte` | analisi PyInstaller da `build_entry.py`, dipendenze Python raggiungibili, manifest generato obbligatorio in `resources`, client OAuth desktop opzionale con nome vincolato; nessun hidden import dichiarato |
| installer | `caronte_installer.py` piu` l'intera directory payload `Caronte` sotto `payload/Caronte`; l'installer copia payload, crea collegamenti e registra il disinstallatore |

Le prove di packaging correnti sono `test_caronte_build.py`,
`test_caronte_installer.py`, `test_build_info.py` e lo smoke locale. Le build
reali restano fuori da questo task.

## Asset e script ritirati

`CONS-G04` ha verificato e ritirato quattro file non raggiungibili dalle
superfici sopra inventariate:

- `local_connector/scripts/generate_caronte_dry_run.py` e
  `local_connector/scripts/imap_readonly_probe.py`, probe standalone storici
  senza entry point, riferimenti correnti o inclusione in wheel/build;
- `Virgilio_1.0.png` e `VirgilioBN_1.0.png`, copie congelate della grafica 1.0
  non referenziate; `Virgilio.png` e `VirgilioBN.png` restano gli asset correnti.

I quattro file sono recuperabili dalla storia Git precedente a `CONS-G04`; gli
script di build, test e operazione sotto `scripts/dev` restano supportati.
