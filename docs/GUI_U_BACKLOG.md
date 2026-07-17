# EPIC GUI-U — Caronte Desktop utente

Stato: `IN_PROGRESS`
Sotto-epica attiva: `GUI-U-E3 - Completamento e distribuzione`
Task corrente: `GUI-U-E3-T02 - Impostazioni essenziali`

Obiettivo finale:

> Distribuire un'applicazione Windows autonoma che possa essere installata, configurata e utilizzata senza Python, virtual environment, CLI, PowerShell, repository, YAML o `.env` visibili all'utente.

Regole operative:

- i task sono eseguiti in ordine di dipendenza, uno per run;
- un task entra in `IN_PROGRESS` solo se possiede tutti gli elementi richiesti dalla Definition of Done;
- le evidenze vengono compilate nella tabella del task, senza creare un documento separato;
- i gate `U-H1`, `U-H2` e `U-H3` richiedono un `PASS` umano esplicito;
- Codex non avvia una sotto-epica bloccata da un gate.

Stati ammessi: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`, `WAITING_FOR_PREVIOUS_TASKS`, `WAITING_HUMAN_REVIEW`, `PASS`.

## GUI-U-E0 — Separazione dal prototipo tecnico

Stato: `DONE`.

### GUI-U-E0-T01 — Congelamento GUI tecnica

Stato: `DONE`
Risultato storico: la GUI esistente e` stata separata dal prodotto. La decisione
umana di `GATE U-H1` abbandona la sua implementazione `gui`/`gui_*`, ma mantiene
`Caronte Manutenzione` come applicazione target con una nuova presentazione.
Dipendenze: nessuna.
Componenti ammessi: entry point e packaging del local connector, modulo GUI esistente, test mirati, documentazione operativa minima.
Esclusioni: nuove tab o funzioni, nuova GUI utente, Apps Script, servizi reali.
Condizione di blocco: il comando o il modulo legacy non possono essere rinominati mantenendo compatibilita` e test mirati nella stessa run.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste il comando `maintenance-gui`. | Test CLI mirato su help e dispatch. | Help CLI verificato; dispatch parametrico `maintenance-gui`/`gui` in `test_maintenance_gui_commands_call_launcher` verde. | `MET` |
| La finestra ha titolo `Caronte Manutenzione`. | Test UI mirato sul titolo della root. | `test_maintenance_gui_identity_and_visible_notice` verifica la chiamata root con titolo esatto. | `MET` |
| E` visibile l'avvertenza che si tratta di uno strumento tecnico. | Test UI sulla stringa visibile. | Lo stesso test verifica testo e posizionamento della label `Strumento tecnico...`. | `MET` |
| `gui`, se mantenuto, e` un alias deprecato. | Test CLI su alias e avviso di deprecazione. | Dispatch comune verificato e avviso `deprecato` catturato su stderr solo per `gui`. | `MET` |
| Non vengono aggiunte tab o funzioni. | Diff circoscritto e test sull'inventario delle tab. | `test_gui_registry_has_required_tabs_and_windows_task_actions` conferma invariato l'inventario di nove tab; diff limitato a identita`, entry point e documentazione. | `MET` |

### GUI-U-E0-T02 — Architettura della nuova applicazione

Stato: `DONE`
Risultato: sono separati `user_app`, nuova `maintenance_gui`, servizi condivisi,
processo in background e packaging; `gui`/`gui_*` sono fuori dall'architettura target.
Dipendenza: `GUI-U-E0-T01 = DONE`.
Componenti ammessi: documentazione architetturale, package layout proposto, entry point e contratti dei servizi.
Esclusioni: implementazione della shell, modifica dei servizi, packaging eseguibile.
Condizione di blocco: non e` possibile definire responsabilita` univoche o un percorso verticale minimo senza una decisione umana di prodotto.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `user_app` non importa il registro delle vecchie nove tab. | Regola architetturale verificabile e controllo import previsto. | `docs/GUI_U_ARCHITETTURA.md` vieta gli import di `maintenance_gui`, `gui` e `gui_*` e definisce i due controlli automatici sugli import. | `MET` |
| GUI e CLI condividono servizi applicativi. | Mappa dei servizi con consumer dichiarati. | La tabella dei contratti dichiara operazioni minime e consumer per sette servizi condivisi. | `MET` |
| Sono definite responsabilita` univoche. | Tabella componenti-responsabilita` senza sovrapposizioni. | La tabella componenti assegna responsabilita` esclusiva e responsabilita` escluse a ogni layer. | `MET` |
| Sono confermate le entry point definitive. | Elenco coerente con `CODEX_STATE.md` e configurazione package prevista. | La tabella conferma `user_app`, `user-gui`, `Caronte.exe`, `maintenance_gui`, `maintenance-gui` e l'eventuale `CaronteManutenzione.exe`; solo `gui`/`gui_*` sono legacy abbandonati. | `MET` |
| E` definito il percorso verticale minimo. | Sequenza primo avvio -> due caselle -> Home -> avvio/pausa. | La sequenza in sei passi copre configurazione assente, Limbo, due caselle, Home, avvio e pausa con arresto controllato. | `MET` |

### GUI-U-E0-T03 — Mappa del codice riutilizzabile

Stato: `DONE`
Risultato: ogni modulo esistente e` classificato come riutilizzabile, adattabile,
legacy abbandonato oppure non importabile nelle nuove presentazioni.
Dipendenza: `GUI-U-E0-T02 = DONE`.
Componenti ammessi: sorgenti e test in lettura, mappa documentale dei moduli e dei servizi.
Esclusioni: refactor, spostamento moduli, modifica di codice o entry point.
Condizione di blocco: un modulo necessario ha responsabilita` non determinabili tramite codice e test esistenti.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Tutti i moduli GUI esistenti sono classificati. | Inventario completo confrontato con i file del package. | `docs/GUI_U_CODE_MAP.md` confronta gli otto file `gui*.py`/`maintenance_gui.py` con i relativi test e assegna a ciascuno una delle quattro categorie. | `MET` |
| Ogni servizio necessario ha una destinazione. | Matrice servizio -> condiviso, utente o manutenzione. | La matrice assegna percorsi, configurazione, credenziali, account, operazioni, supervisore, attivita`, avvio Windows e manutenzione ai layer target e indica i consumer. | `MET` |
| Le lacune applicative sono elencate. | Elenco finito associato ai task E1-E3. | La sezione `Lacune applicative finite` copre senza voci generiche tutti e soli i task `GUI-U-E1-T01..T04`, `E2-T01..T06` ed `E3-T01..T06`. | `MET` |
| Nessun comando CLI viene automaticamente convertito in pulsante. | Revisione della mappa rispetto alle attivita` utente. | La matrice attivita` -> composizione parte da sei attivita` utente ed esclude esplicitamente comandi, argomenti, output e registro delle nove tab. | `MET` |
| Il primo task di fondazione e` definito. | Scheda E1-T01 confermata completa secondo DoD. | Verificata la scheda `GUI-U-E1-T01`: risultato, cinque criteri binari con prove, dipendenza, componenti, esclusioni e blocco sono presenti; resta vincolata al `PASS` umano. | `MET` |

### GATE U-H1 — Approvazione umana dell'architettura

Stato: `PASS`.

Il gate puo` passare a `WAITING_HUMAN_REVIEW` solo dopo la chiusura di E0-T01, E0-T02 ed E0-T03. Codex non puo` dichiararlo `PASS`.

La verifica umana riguarda:

- confini prodotto/manutenzione;
- nomi;
- mappa dei servizi;
- percorso verticale minimo.

GUI-U-E1 non puo` iniziare prima del `PASS` esplicito.

Riepilogo per il collaudo umano:

- `GUI-U-E0-T01`, `GUI-U-E0-T02` e `GUI-U-E0-T03` sono `DONE`;
- `docs/GUI_U_ARCHITETTURA.md` fissa confini, nomi, contratti e percorso minimo;
- `docs/GUI_U_CODE_MAP.md` classifica gli otto moduli GUI, assegna i servizi e
  collega le lacune ai task E1-E3.

Esito umano del 2026-07-15: `PASS` su nomi, mappa dei servizi e percorso
verticale minimo, con una correzione vincolante sui confini: l'implementazione
legacy `gui`/`gui_*` e` abbandonata, mentre `Caronte Manutenzione` resta
un'applicazione target e ricevera` una nuova presentazione separata. La
documentazione architetturale, la mappa del codice e i task successivi recepiscono
la decisione; nessuna modifica di codice appartiene a questo gate documentale.

## GUI-U-E1 — Fondazioni applicative

Stato: `DONE`.

### GUI-U-E1-T01 — Percorsi applicativi Windows

Stato: `DONE`
Risultato: configurazione e dati usano percorsi applicativi Windows indipendenti dal repository.
Dipendenza: `GATE U-H1 = PASS`.
Componenti ammessi: servizio percorsi, configurazione, test con filesystem temporaneo, documentazione minima.
Esclusioni: widget, credenziali, installer, migrazione automatica di dati reali.
Condizione di blocco: manca una policy approvata per directory dati/configurazione o non e` possibile sostituire i percorsi nei test.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Dati e configurazione usano directory applicative definite. | Test unitari sulle risoluzioni Windows. | `ApplicationPaths` risolve configurazione in `%APPDATA%\Caronte\config.yaml` e dati in `%LOCALAPPDATA%\Caronte`; test dedicato verde. | `MET` |
| Nessun percorso del repository e` necessario. | Test di avvio con repository non presente nel path applicativo. | Test da directory estranea conferma che config e dati non discendono dal repository o dalla cwd. | `MET` |
| I percorsi sono sostituibili nei test. | Test con root temporanea iniettata. | Root config/dati iniettate e create sotto `tmp_path`; i test CLI che scrivono stato impostano una root temporanea. | `MET` |
| L'avvio da directory differente funziona. | Test di processo da working directory temporanea. | Sottoprocesso Python avviato da cwd temporanea risolve entrambe le directory Windows attese. | `MET` |
| Esistono test mirati. | Comando e risultato dei test registrati qui. | `pytest ... test_application_paths.py` -> `6 passed`; regressioni mirate -> `9 passed`; suite e smoke -> `359 passed`. | `MET` |

### GUI-U-E1-T02 — Modello unico di configurazione

Stato: `DONE`
Risultato: un modello strutturale unico e indipendente dalla GUI governa la configurazione.
Dipendenza: `GUI-U-E1-T01 = DONE`.
Componenti ammessi: servizi configurazione condivisi, adapter di persistenza, CLI compatibile, test sintetici.
Esclusioni: widget, backend credenziali Windows, rete reale.
Condizione di blocco: due fonti esistenti non possono essere riconciliate atomicamente senza migrazione separata.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste una sola fonte autorevole per ogni dato. | Test di round-trip e mappa campo -> fonte. | `test_round_trip_has_one_authoritative_source_and_two_accounts` verifica round-trip e mappa `accounts.*`/`storage.*` verso lo stesso file strutturale. | `MET` |
| Il modello e` indipendente dai widget. | Test import del servizio senza toolkit GUI. | `test_service_import_does_not_require_a_gui_toolkit` ricarica il modulo rifiutando import Tkinter, PySide e PyQt. | `MET` |
| I servizi sono riutilizzabili dalla CLI. | Test CLI mirato sul servizio condiviso. | `test_scan_cli_uses_shared_configuration_service` verifica che `scan-imap-accounts` carichi gli account tramite `ConfigurationService`. | `MET` |
| La scrittura e` atomica. | Test di errore con rollback e file integro. | `test_atomic_write_failure_preserves_existing_file` forza il fallimento del replace e conferma byte invariati. | `MET` |
| Sono supportati almeno due account. | Test round-trip con due account distinti. | Il round-trip mirato salva e ricarica `account_1` e `account_2`; test task `4 passed`, suite e smoke `363 passed`. | `MET` |

### GUI-U-E1-T03 — Archivio credenziali astratto

Stato: `DONE`
Risultato: le credenziali sono gestite tramite un contratto astratto separato dal modello strutturale.
Dipendenza: `GUI-U-E1-T02 = DONE`.
Componenti ammessi: interfaccia `CredentialStore`, fake store, servizi account, test sintetici.
Esclusioni: adapter Windows reale, widget, credenziali reali o remote.
Condizione di blocco: il modello strutturale richiede ancora il valore della password anziche` un riferimento.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste `CredentialStore`. | Test del contratto pubblico. | `test_fake_store_implements_public_contract_and_crud` usa il fake attraverso il protocollo pubblico; test task `7 passed`. | `MET` |
| Supporta salva, leggi, aggiorna e cancella. | Test CRUD parametrico. | Test parametrico sul fake: creazione, lettura, aggiornamento, cancellazione ed errori tipizzati verificati. | `MET` |
| Esiste un fake store. | Test servizi account senza backend di sistema. | `AccountCredentialService` verificato con `FakeCredentialStore`, senza import o chiamate a backend di sistema. | `MET` |
| Supporta credenziali distinte per almeno due account. | Test isolamento di due riferimenti. | Due account sintetici conservano valori distinti; modifica del primo e rimozione del secondo restano isolate. | `MET` |
| Nessuna password compare nei file strutturali o nei log. | Scanner mirato su file e output di test. | Test mirato verifica quattro valori sentinella assenti da YAML strutturale, log, rappresentazioni ed errori; scansione segreti finale verde. | `MET` |

### GUI-U-E1-T04 — Backend credenziali Windows

Stato: `DONE`
Risultato: `CredentialStore` dispone di un adapter Windows sicuro e sostituibile.
Dipendenza: `GUI-U-E1-T03 = DONE`.
Componenti ammessi: adapter credenziali Windows, factory del servizio, traduzione errori, test mock/fake.
Esclusioni: credenziali reali, GUI completa, sincronizzazione tra PC.
Condizione di blocco: il backend scelto richiede segreti versionati, privilegi amministrativi o rete.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste un adapter Windows. | Test del contratto con API di sistema mockata. | `test_windows_adapter_contract_uses_mocked_system_api` verifica CRUD e target `Caronte/` tramite porta mockata. | `MET` |
| Il modello conserva solo riferimenti. | Test di persistenza e scansione dei file. | Due account strutturali conservano solo riferimenti; quattro valori sintetici sono assenti da YAML e rappresentazioni. | `MET` |
| La rimozione dell'account elimina la relativa credenziale. | Test servizio remove con verifica backend. | La factory condivisa rimuove dal backend mock sia il riferimento utente sia il riferimento password. | `MET` |
| Gli errori sono traducibili in messaggi utente. | Test delle eccezioni tipizzate e dei messaggi. | Errori not-found, duplicato e accesso negato sono tipizzati e tradotti in messaggi sicuri senza valori sensibili. | `MET` |
| I test non usano credenziali reali. | Fixture fake e controllo assenza accessi reali. | Sei casi sintetici usano esclusivamente `MockWindowsCredentialApi`; nessuna API nativa, rete o credenziale reale. | `MET` |

## GUI-U-E2 — Percorso verticale minimo

Stato: `IN_PROGRESS`.

### GUI-U-E2-T01 — Nuova shell `user_app`

Stato: `DONE`
Risultato: esiste una shell utente indipendente che apre il primo avvio o la Home.
Dipendenza: `GUI-U-E1-T04 = DONE`.
Componenti ammessi: modulo `user_app`, entry point `user-gui`, shell e routing minimo, test UI.
Esclusioni: import di `maintenance_gui`, vecchie tab, funzionalita` operative non previste.
Condizione di blocco: la shell richiede l'import del registro della GUI tecnica o non puo` distinguere configurazione presente/assente.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste il comando `user-gui`. | Test CLI su help e dispatch. | `test_user_gui_help_and_dispatch`: help espone il comando e il dispatch chiama `launch_user_app` con configurazione iniettata. | `MET` |
| La finestra ha titolo `Caronte`. | Test UI sul titolo della root. | `test_shell_has_caronte_title_and_routes_missing_configuration_to_first_run`: root con titolo esatto `Caronte`. | `MET` |
| Non importa `maintenance_gui`. | Test import e scansione dipendenze. | `test_user_app_imports_no_technical_or_legacy_presentation`: AST di tutto `user_app` privo di import `maintenance_gui`, `gui` o `gui_*`. | `MET` |
| Non contiene nessuna delle nove vecchie tab. | Test inventario widget/viste. | `test_user_view_inventory_excludes_legacy_tabs_and_forbidden_terms`: inventario limitato a `Primo avvio` e `Home`, disgiunto dalle nove tab. | `MET` |
| Configurazione assente porta al primo avvio. | Test UI con directory dati vuota. | `test_shell_has_caronte_title_and_routes_missing_configuration_to_first_run`: file assente instrada a `UserRoute.FIRST_RUN`; file presente instrada a Home nel test complementare. | `MET` |

### GUI-U-E2-T02 — Wizard con schermate reali

Stato: `DONE`
Risultato: il wizard usa schermate sostituite realmente, con navigazione e validazione locale al passo.
Dipendenza: `GUI-U-E2-T01 = DONE`.
Componenti ammessi: viste Benvenuto e Limbo, controller navigazione, validatori, test UI.
Esclusioni: configurazione caselle, Home, rete o filesystem reale fuori fixture.
Condizione di blocco: il toolkit non consente di verificare deterministicamente sostituzione e ripristino dei frame.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Benvenuto e Limbo sono frame distinti. | Test UI su classi/istanze delle viste. | `test_wizard_uses_distinct_welcome_and_limbo_frames`: classi e frame delle due viste sono distinti. | `MET` |
| `Continua` sostituisce realmente i widget. | Test visibilita` dopo navigazione avanti. | `test_continue_replaces_widgets_and_back_restores_welcome_frame`: il frame Benvenuto viene distrutto passando a Limbo. | `MET` |
| `Indietro` ripristina il frame precedente. | Test stato e visibilita` dopo ritorno. | Lo stesso test verifica il ritorno a un nuovo frame Benvenuto visibile e lo stato `WELCOME`. | `MET` |
| Ogni passaggio valida solo i propri dati. | Test unitari dei validatori per passo. | `test_each_step_validator_checks_only_its_own_data`: Benvenuto non richiede dati; Limbo valida solo il percorso inserito. | `MET` |
| I widget precedenti non restano visibili. | Test automatico sull'albero widget. | Il test avanti/indietro verifica `destroy()` su entrambi i frame sostituiti e un solo frame corrente non distrutto. | `MET` |

### GUI-U-E2-T03 — Configurazione semplificata di una casella

Stato: `DONE`
Risultato: una casella viene configurata con campi ordinari e dettagli tecnici richiudibili.
Dipendenza: `GUI-U-E2-T02 = DONE`.
Componenti ammessi: vista account del wizard, servizi account/configurazione/credenziali, fake IMAP, test UI.
Esclusioni: seconda casella, controllo operativo, rete reale.
Condizione di blocco: il provider non puo` essere configurato senza mostrare un termine vietato nella vista ordinaria.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| I campi iniziali sono nome, email, password e stato attivo. | Test UI sull'inventario dei campi visibili. | `test_account_step_starts_with_only_ordinary_fields_visible`: inventario iniziale limitato ai quattro campi e password mascherata. | `MET` |
| Gmail/Workspace precompila host e porta. | Test UI sui default provider. | `test_gmail_workspace_prefills_server_and_port`: default `imap.gmail.com` e porta `993`. | `MET` |
| Le impostazioni avanzate sono richiudibili. | Test apertura/chiusura pannello. | `test_advanced_account_settings_can_be_opened_and_closed`: pannello inizialmente nascosto, apribile e richiudibile. | `MET` |
| Esiste un test read-only separato. | Test con fake IMAP che rifiuta mutazioni. | `test_connection_service_uses_only_readonly_listing` e `test_account_connection_check_uses_separate_readonly_port`: servizio/callback separati, unica operazione mailbox `list_pending`, nessuna mutazione. | `MET` |
| Nessun termine tecnico vietato e` visibile. | Test automatico sulle stringhe visibili. | `test_account_view_has_no_forbidden_technical_terms`: scansione automatica delle label e azioni visibili disgiunta dall'elenco vietato. | `MET` |

### GUI-U-E2-T04 — Multi-account

Stato: `DONE`
Risultato: l'utente gestisce almeno due caselle persistenti e indipendenti.
Dipendenza: `GUI-U-E2-T03 = DONE`.
Componenti ammessi: tabella caselle, CRUD account, servizi condivisi, fake credential store, test UI.
Esclusioni: controllo continuo, Home completa, rete reale.
Condizione di blocco: il modello o l'archivio credenziali non garantisce isolamento tra account.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste la tabella delle caselle. | Test UI su colonne e righe sintetiche. | `test_mailbox_table_has_expected_columns_and_two_synthetic_rows`: colonne Nome casella, Email, Provider e Stato con due righe sintetiche. | `MET` |
| Sono disponibili aggiunta, modifica e rimozione. | Test UI del ciclo CRUD. | `test_account_crud_supports_different_providers_and_separate_credentials`: ciclo aggiunta di due caselle, modifica della prima e rimozione della seconda. | `MET` |
| Sono supportati server o provider differenti. | Test con due configurazioni diverse. | Lo stesso test persiste una casella Gmail/Workspace e una `custom_imap` con host differente. | `MET` |
| Le credenziali sono separate. | Test sui riferimenti e fake store. | Lo stesso test verifica riferimenti distinti e due password indipendenti nel fake store. | `MET` |
| I dati persistono dopo chiusura e riapertura. | Test round-trip della shell. | `test_two_accounts_persist_after_shell_is_closed_and_reopened`: nuova istanza di configurazione e shell ritrova entrambe le caselle e apre Home. | `MET` |

### GUI-U-E2-T05 — Home minima

Stato: `DONE`
Risultato: la Home mostra stato essenziale e tre azioni comprensibili.
Dipendenza: `GUI-U-E2-T04 = DONE`.
Componenti ammessi: vista Home, view model stato, servizi runner fake, test UI.
Esclusioni: tabella attivita`, impostazioni complete, output tecnico.
Condizione di blocco: lo stato operativo non e` disponibile tramite un servizio indipendente dalla GUI tecnica.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| E` visibile lo stato generale. | Test UI sui principali stati sintetici. | `test_home_renders_main_general_states` verifica `Pronto`, controllo in corso, pausa e attenzione. | `MET` |
| E` visibile il numero di caselle attive. | Test view model con due account. | `test_home_status_service_counts_only_active_accounts` conta due caselle attive e ne esclude una disattivata. | `MET` |
| E` visibile l'ultimo controllo. | Test rendering timestamp Europe/Rome. | `test_home_renders_last_check_in_europe_rome` converte `08:05 UTC` in `10:05` Europe/Rome. | `MET` |
| Esistono `Controlla ora`, `Avvia` e `Pausa`. | Test UI sulle tre azioni. | `test_home_has_exactly_the_three_primary_actions` verifica le tre azioni e nessun'altra. | `MET` |
| Non compare JSON o output CLI. | Test automatico sulle stringhe visibili. | `test_home_contains_no_technical_output_or_forbidden_terms` verifica testo visibile e termini vietati. | `MET` |

### GUI-U-E2-T06 — Avvio, pausa e arresto

Stato: `DONE`
Risultato: controllo singolo e continuo sono non bloccanti e hanno ciclo di vita deterministico.
Dipendenza: `GUI-U-E2-T05 = DONE`.
Componenti ammessi: runner/worker condiviso, coda eventi, controller Home, fake lenti, test di concorrenza.
Esclusioni: servizi reali, nuove azioni operative, processo Windows residente.
Condizione di blocco: il runner esistente non puo` essere controllato senza duplicare logica o lasciare processi orfani.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Il controllo singolo e` non bloccante. | Test con fake lento e verifica reattivita`. | `test_check_now_returns_before_slow_worker_finishes`: il comando ritorna mentre il fake e` ancora bloccato. | `MET` |
| Il controllo continuo e` non bloccante. | Test start con fake worker. | `test_continuous_start_returns_before_slow_worker_finishes`: avvio accettato e worker ancora attivo. | `MET` |
| La pausa e` funzionante. | Test stop e stato finale. | `test_pause_stops_active_worker_and_reaches_final_state`: terminate ricevuto e stato finale `stopped`. | `MET` |
| Non puo` partire un doppio processo. | Test doppio start concorrente. | `test_concurrent_second_start_is_rejected`: seconda richiesta rifiutata con evento dedicato. | `MET` |
| Non resta un processo orfano alla chiusura. | Test close con worker attivo. | `test_close_kills_unresponsive_worker_and_leaves_no_orphan`: fallback kill eseguito e stato `stopped`. | `MET` |

### GUI-U-E2-T07 — Correzioni dal collaudo verticale

Stato: `DONE`.
Risultato: il primo avvio termina in modo esplicito, la configurazione resta
rivedibile dalla Home e i controlli booleani e di finestra hanno comportamento
coerente con quanto mostrato.
Dipendenza: `GUI-U-E2-T06 = DONE`; esito umano negativo di `GATE U-H2` del 2026-07-16.
Componenti ammessi: shell e viste `user_app`, navigazione, servizi applicativi
gia` condivisi e test UI mirati.
Esclusioni: servizi reali, packaging, nuove funzioni operative, GUI legacy,
modifiche ai nomi definitivi o all'architettura approvata.
Condizione di blocco: una correzione richiede di cambiare il percorso utente o
l'architettura oltre le osservazioni approvate nel collaudo.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `Casella attiva` ha uno stato iniziale binario e il valore salvato coincide con quello mostrato. | Test UI e round-trip su stato selezionato e non selezionato. | `test_active_mailbox_state_is_binary_visible_and_persisted`: selezione iniziale visibile e round-trip `true`/`false`. | `MET` |
| Dopo il salvataggio delle caselle esiste una conclusione esplicita del wizard che porta alla Home nella stessa sessione. | Test di navigazione completo senza chiusura e riapertura. | `test_first_run_finishes_explicitly_on_home_without_restart`: `Termina configurazione` porta alla Home senza riavvio. | `MET` |
| Dalla Home si puo` riaprire la configurazione esistente, correggere un dettaglio e tornare alla Home. | Test UI di riapertura, modifica e persistenza. | `test_home_reopens_existing_configuration_and_returns_after_edit`: valori e credenziale ricaricati, modifica persistita, ritorno Home. | `MET` |
| Chiusura e riduzione a icona sono chiaramente disponibili e funzionanti nelle viste utente. | Test sui controlli finestra e sulla chiusura controllata del worker. | `test_window_controls_are_visible_and_close_owned_worker`: controlli visibili, `iconify`, arresto worker e distruzione finestra. | `MET` |
| Restano assenti termini tecnici, percorsi del repository e viste legacy. | Test automatico sull'inventario completo dei testi visibili. | `test_complete_visible_text_inventory_has_no_technical_or_legacy_terms`: inventario completo privo di stringhe vietate e viste legacy. | `MET` |

### GATE U-H2 — Collaudo umano del percorso verticale

Stato: `PASS`.

Prerequisiti verificati: `GUI-U-E2-T01` - `GUI-U-E2-T07` sono `DONE`; test
mirati T07 `5 passed`, regressione GUI utente `36 passed`, suite local connector
e smoke `409 passed`.

`PASS` registrato il 2026-07-16 su conferma umana esplicita dopo il nuovo
collaudo del percorso corretto. Codex non ha approvato autonomamente il gate.

Esito umano del 2026-07-16: `FAIL`. Il percorso principale funziona e non
mostra termini tecnici o percorsi del repository, ma il collaudo ha rilevato:

- stato iniziale indeterminato di `Casella attiva` e semantica salvata invertita;
- assenza di una conclusione esplicita del wizard verso la Home;
- assenza di un accesso dalla Home per rivedere la configurazione;
- assenza di controlli chiaramente visibili per chiudere o ridurre la finestra.

Azione necessaria: nessuna; il gate e` chiuso.

Scenario umano:

1. avvio GUI;
2. selezione Limbo;
3. configurazione di due caselle;
4. conclusione esplicita verso la Home senza riavvio;
5. riapertura delle impostazioni dalla Home, modifica e ritorno alla Home;
6. controllo manuale;
7. avvio;
8. pausa;
9. riduzione a icona e chiusura.

Condizioni:

- nessun terminale;
- nessuna modifica manuale di file;
- nessuna documentazione tecnica necessaria;
- nessun termine vietato visibile.

GUI-U-E3 non puo` iniziare prima del nuovo `PASS` esplicito.

## GUI-U-E3 — Completamento e distribuzione

Stato: `IN_PROGRESS`.

### GUI-U-E3-T01 — Attivita` e problemi

Stato: `DONE`
Risultato: attivita` e problemi sono leggibili e orientati all'azione.
Dipendenza: `GATE U-H2 = PASS`.
Componenti ammessi: vista attivita`, proiezione eventi, filtri, dettaglio tecnico separato, test UI.
Esclusioni: nuovi eventi di dominio, modifica pipeline, dati reali.
Condizione di blocco: gli eventi esistenti non possono essere tradotti senza esporre dati sensibili o dettagli tecnici nella vista ordinaria.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste una tabella attivita`. | Test UI su colonne e righe sintetiche. | `test_activity_view_has_table_filters_and_no_json`: sei colonne utente e riga sintetica proiettata. | `MET` |
| Esistono filtri essenziali. | Test combinazioni casella, esito e data. | `test_activity_view_applies_account_outcome_and_date_filters` e test applicativo combinano i tre filtri. | `MET` |
| Non compare JSON. | Test sulle stringhe e celle visibili. | Test servizio/vista escludono payload, segreti, path e delimitatori JSON dai valori visibili. | `MET` |
| Ogni problema contiene un'azione consigliata. | Test su catalogo errori rappresentativo. | Errori e conflitti sintetici producono azioni distinte e verificabili. | `MET` |
| I dettagli tecnici sono separati. | Test UI su pannello avanzato chiuso per default. | Il pannello e` nascosto al primo render e si apre solo su riga selezionata. | `MET` |

### GUI-U-E3-T02 — Impostazioni essenziali

Stato: `DONE`
Risultato: le preferenze ordinarie sono modificabili senza esporre parametri tecnici.
Dipendenza: `GUI-U-E3-T01 = DONE`.
Componenti ammessi: vista impostazioni, modello configurazione condiviso, servizi avvio/chiusura, test UI.
Esclusioni: configurazione Bucoliche, manutenzione, installer.
Condizione di blocco: una preferenza non ha una fonte autorevole unica o richiede modifica manuale di file.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| E` configurabile il Limbo. | Test UI e persistenza con directory temporanea. | `test_limbo_interval_and_preferences_round_trip_through_shared_model`: la directory temporanea scelta e` riletta da `storage.staging_dir`; `test_settings_view_saves_preferences_and_updates_close_behavior`: salvataggio dalla vista. | `MET` |
| E` configurabile l'intervallo. | Test validazione e round-trip. | `test_limbo_interval_and_preferences_round_trip_through_shared_model` verifica il round-trip a 720 secondi; `test_interval_validation_rejects_values_outside_allowed_range` copre valori vuoti, non numerici e limiti. | `MET` |
| E` configurabile l'avvio automatico. | Test con adapter Windows fake. | `test_windows_startup_adapter_uses_injected_registry_without_real_access` verifica abilita/disabilita con registro iniettato; il round-trip usa `FakeStartupAdapter` senza accessi reali. | `MET` |
| E` configurabile il comportamento alla chiusura. | Test controller sui comportamenti ammessi. | `test_settings_view_saves_preferences_and_updates_close_behavior` verifica riduzione a icona sul controllo finestra e chiusura esplicita con arresto del worker. | `MET` |
| I parametri tecnici sono confinati alle impostazioni avanzate. | Test sulle stringhe visibili di default. | `test_default_settings_view_hides_technical_parameters` verifica l'assenza completa dei termini vietati nella vista ordinaria. | `MET` |

### GUI-U-E3-T03 — Bucoliche e avvio Windows

Stato: `DONE`
Risultato: Bucoliche e avvio automatico sono configurabili tramite percorsi guidati e stati comprensibili.
Dipendenza: `GUI-U-E3-T02 = DONE`.
Componenti ammessi: servizi Bucoliche e Task Scheduler condivisi, viste guidate, adapter fake, test UI.
Esclusioni: servizi Google reali, credenziali reali, nuove architetture residenti.
Condizione di blocco: un'azione non possiede un servizio applicativo stabile e testabile senza accesso reale.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Bucoliche e` attivabile e disattivabile. | Test UI e persistenza. | `test_bucoliche_activation_and_deactivation_persist_without_changing_other_sections`: round-trip e sezione unica. | `MET` |
| Il collegamento Google e` guidato. | Test del percorso con adapter fake. | `test_google_connection_is_a_guided_step_using_only_the_injected_adapter`: percorso numerato e gateway fake. | `MET` |
| Il registro e` verificabile. | Test read-only con fake client. | `test_register_verification_is_read_only_through_the_injected_adapter`: file invariato e sola lettura fake. | `MET` |
| Avvio automatico installabile e rimovibile. | Test con adapter Task Scheduler fake. | `test_automatic_control_install_remove_and_status_use_fake_scheduler`: stato, installazione e rimozione. | `MET` |
| Lo stato e` comprensibile. | Test dei messaggi per stati ed errori noti. | `test_guided_view_shows_clear_steps_and_known_error_messages` e traduzione errori: messaggi azionabili, nessun dettaglio interno. | `MET` |

### GUI-U-E3-T04 — Manutenzione avanzata

Stato: `DONE`
Risultato: `Caronte Manutenzione` espone le operazioni tecniche tramite una nuova
presentazione protetta, separata dall'implementazione legacy.
Dipendenza: `GUI-U-E3-T03 = DONE`.
Componenti ammessi: `maintenance_gui`, nuova presentazione manutenzione, servizi backup/integrita`/diagnostica/reset, test fake.
Esclusioni: import o nuove funzioni in `gui`/`gui_*`, cancellazioni non confermate, dati reali.
Condizione di blocco: un'operazione distruttiva non offre backup, conferma o risultato verificabile.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste il backup. | Test su directory temporanea e contenuto prodotto. | `test_backup_copies_directory_and_content`: copia sibling di 2 file sintetici, contenuto e sorgente verificati. | `MET` |
| Esiste la verifica integrita`. | Test su stato valido e corrotto sintetico. | `test_integrity_reports_valid_and_corrupt_synthetic_databases`: archivio inizializzato `valid`, byte non validi `corrupt`. | `MET` |
| Esiste il report diagnostico. | Test di redazione e contenuti minimi. | `test_diagnostic_report_has_minimum_content_and_redacts`: metadati minimi presenti e valore/chiave sensibili redatti. | `MET` |
| Il reset e` protetto. | Test su conferma, annullamento e backup. | `test_reset_requires_confirmation_and_creates_backup`: annullamento conserva i dati; conferma crea backup leggibile e ricrea la baseline. | `MET` |
| `Caronte Manutenzione` usa la nuova presentazione senza import legacy. | Test UI, import e inventario della build. | `test_new_maintenance_presentation_has_only_supported_operations_and_no_legacy_import`: titolo, quattro operazioni, protezione reset e AST import verdi; suite/smoke `433 passed`. | `MET` |

### GUI-U-E3-T05 — Build autonoma

Stato: `DONE`
Risultato: una build one-folder riproducibile avvia Caronte senza ambiente di sviluppo.
Dipendenza: `GUI-U-E3-T04 = DONE`.
Componenti ammessi: configurazione build, risorse, entry point utente, smoke della build, documentazione di build.
Esclusioni: installer, pubblicazione, firma codice, modifica Apps Script.
Condizione di blocco: la build richiede repository, runtime esterno o file non dichiarati.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| La build one-folder e` riproducibile. | Due build pulite con inventario equivalente. | Due build PyInstaller pulite con epoch e hash seed fissati: `1582` file per cartella e `0` differenze su percorso, dimensione e SHA-256. | `MET` |
| Il runtime e` incluso. | Avvio su ambiente di test senza runtime installato. | La cartella include Python 3.13, Tcl/Tk e `tzdata`; lo smoke avvia la copia su Windows privo di Python registrate dal launcher. | `MET` |
| Non e` richiesto un venv. | Smoke da shell priva dell'ambiente di sviluppo. | `smoke_caronte_build.ps1` azzera `VIRTUAL_ENV` e `PYTHONPATH`; la copia si avvia correttamente. | `MET` |
| Non e` richiesto il repository. | Smoke dopo copia della sola cartella build. | Lo smoke copia esclusivamente `dist/Caronte` in una directory temporanea, cambia directory di lavoro e completa l'avvio. | `MET` |
| L'avvio avviene da `Caronte.exe`. | Test di processo e titolo finestra. | Processo `Caronte.exe` vivo e finestra con titolo esatto `Caronte`; test entry point e comando worker congelato verdi. | `MET` |

### GUI-U-E3-T06 — Installer Windows

Stato: `DONE`
Risultato: Caronte e` installabile e disinstallabile con dati separati dal programma.
Dipendenza: `GUI-U-E3-T05 = DONE`.
Componenti ammessi: configurazione installer, artefatto build, collegamento Start, test su VM/ambiente isolato.
Esclusioni: distribuzione pubblica, firma commerciale, aggiornamento automatico.
Condizione di blocco: l'installer richiede privilegi o dipendenze non dichiarati, oppure mescola dati utente e file programma.

Sblocco 2026-07-17: ricevuta autorizzazione umana esplicita, predisposta una
toolchain completa con Tcl/Tk nella cartella di build ignorata e completati build
e collaudo isolato del setup per utente, che non richiede privilegi in esecuzione.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| L'installer funziona. | Installazione pulita su VM Windows. | Prodotto `CaronteSetup.exe` (`30.594.909` byte, SHA-256 `810C35C61E6E42062FBEE9BEAB870A2AB62E8F9192422A010695851155632043`); smoke su profilo Windows isolato con riferimenti Python rimossi: installazione silenziosa completata e programma avviabile. | `MET` |
| Esiste il collegamento nel menu Start. | Verifica automatica/manuale del collegamento. | Lo smoke crea e verifica `Caronte.lnk` nella cartella Start del profilo isolato. | `MET` |
| La directory dati e` separata. | Verifica path dopo primo avvio. | Programma in `LOCALAPPDATA/Programs/Caronte`, configurazione in `APPDATA/Caronte` e dati in `LOCALAPPDATA/Caronte`; test unitario e smoke confermano tre radici distinte. | `MET` |
| La disinstallazione funziona. | Verifica rimozione programma e policy dati. | Lo smoke verifica registrazione e rimozione del disinstallatore, programma, collegamento e voce HKCU; configurazione e dati sintetici restano presenti. | `MET` |
| Il wizard parte alla prima apertura. | Avvio su profilo utente nuovo. | Con profilo isolato privo di configurazione, `Caronte.exe` resta attivo e mostra la finestra `Caronte`; i test di routing confermano il percorso di primo avvio. | `MET` |

### GATE U-H3 — Collaudo umano di distribuzione

Stato: `WAITING_HUMAN_REVIEW`.

Codex non puo` dichiararlo `PASS`.

Prerequisiti verificati: `GUI-U-E3-T01` - `GUI-U-E3-T06 = DONE`; test mirati
installer `9 passed`, suite local connector `442 passed`, smoke locale
`442 passed` e smoke installer isolato completato con dati sintetici preservati.

Scenario su PC o VM senza Python:

1. installazione;
2. primo avvio;
3. due caselle;
4. controllo;
5. pausa;
6. chiusura e riapertura;
7. persistenza;
8. avvio automatico;
9. disinstallazione.

La EPIC GUI-U puo` essere chiusa solo dopo il `PASS` umano.
