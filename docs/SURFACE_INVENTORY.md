# Inventario delle superfici raggiungibili

Stato verificato per `CONS-G01` il 2026-07-28. L'inventario descrive la
raggiungibilita` statica della release 1.1.0; non dichiara supportate le
superfici sperimentali o deprecate che risultano ancora collegate al parser.

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

Tutti i parser elencati hanno un ramo esplicito in `__main__.main`.

| Comandi | Dispatch diretto |
| --- | --- |
| `send-caronte-dry-run` | `CaronteDryRunHttpClient.send_ready_attachment` |
| `stage-ready-files`, `verify-drive-staging`, `intake-drive-staging-test`, `intake-da-archiviare` | rispettivamente `LocalDriveStagingTransport`, `DriveStagingVerifyClient`, `DriveStagingIntakeTestClient`, `DaArchiviareIntakeHttpClient` |
| `litellm-gateway-dry-run` | `LiteLLMGateway.complete` (sperimentale; `CONS-G03`) |
| `classify-manifest-dry-run`, `review-classification-dry-run`, `classification-feedback-dry-run` | funzioni di proposta, revisione e feedback in `classification` (sperimentali; `CONS-G03`) |
| `compare-parser-fixtures`, `extract-local-fixtures` | funzioni in `parser_spike` (sperimentali; `CONS-G03`) |
| `scan-imap-accounts`, `process-imap-accounts`, `stage-ready-attachments` | scanner/processore multi-account e `LocalFilesystemStorageAdapter` |
| `complete-staged-messages`, `ack-completed-messages` | `LocalCompletionRunner`, `ControlledAckRunner` |
| `run-local-pipeline` | `LocalPipelineRunner.run` |
| `watch`, `local-watch` | ciclo su pipeline locale; `local-watch` e` alias di sviluppo |
| `doctor`, `check-local-conflicts` | `LocalDoctor.run`, `LocalConflictChecker.run` |
| `export-central-events`, `export-registro-events` | funzioni omonime in `traceability` |
| `export-to-bucoliche`, `refresh-bucoliche-state`, `doctor-bucoliche` | `BucolicheAppendOnlyAdapter` e `BucolicheDoctor` |
| `pilot-check`, `pilot-run-safe`, `pilot-run`, `pilot`, `pilot-preview` | servizi `PilotCheck`, `PilotSafeRunner`, `PilotRunV11Runner`, `PilotPreview` |
| `setup-bucoliche-test-sheet`, `google-oauth-login` | `BucolicheSheetSetup`, `GoogleOAuthLogin` |
| `init-config` | `scaffold_local_config` |
| `install-windows-task`, `status-windows-task`, `uninstall-windows-task` | funzioni in `windows_task` |
| `reset-local-state` | `reset_local_state` |
| `user-gui` | `user_app.launch_user_app` |
| `maintenance-gui` | `maintenance_gui.launch_gui` |

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
- Il package root `virgilio_connector.__init__` riesporta una API ampia; la sua
  riduzione e` riservata a `CONS-C01`.

## Contenuto di package e build

| Artefatto | Inclusione verificata |
| --- | --- |
| wheel | package trovati sotto `local_connector/src`; metadata, dipendenze e `virgilio` definiti da `pyproject.toml`; nessun `package_data` esplicito |
| distribuzione `Caronte` | analisi PyInstaller da `build_entry.py`, dipendenze Python raggiungibili, manifest generato obbligatorio in `resources`, client OAuth desktop opzionale con nome vincolato; nessun hidden import dichiarato |
| installer | `caronte_installer.py` piu` l'intera directory payload `Caronte` sotto `payload/Caronte`; l'installer copia payload, crea collegamenti e registra il disinstallatore |

Le prove di packaging correnti sono `test_caronte_build.py`,
`test_caronte_installer.py`, `test_build_info.py` e lo smoke locale. Le build
reali restano fuori da questo task.
