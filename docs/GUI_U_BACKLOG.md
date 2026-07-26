# EPIC GUI-U — Caronte Desktop utente

Stato: `IN_PROGRESS`
Fase attiva: `GUI-U-R - Recupero prodotto e collaudo osservabile`
Task completato: `GUI-U-R03-R06 - Consegna operativa a Da archiviare`
Successivo: `GUI-U-R04-R03 - Notifica operativa e accesso a Virgilio`

Obiettivo finale:

> Distribuire un'applicazione Windows autonoma che possa essere installata, configurata e utilizzata senza Python, virtual environment, CLI, PowerShell, repository, YAML o `.env` visibili all'utente.

Regole operative:

- i task sono eseguiti in ordine di dipendenza, uno per run;
- un task entra in `IN_PROGRESS` solo se possiede tutti gli elementi richiesti dalla Definition of Done;
- le evidenze vengono compilate nella tabella del task, senza creare un documento separato;
- i gate `U-H1`, `U-H2` e `U-H3` richiedono un `PASS` umano esplicito;
- Codex non avvia una sotto-epica bloccata da un gate.

Stati ammessi: `TODO`, `IN_PROGRESS`, `DONE`, `IMPLEMENTED_NOT_ACCEPTED`, `BLOCKED`, `WAITING_FOR_PREVIOUS_TASKS`, `WAITING_HUMAN_REVIEW`, `PASS`.

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

Stato: `DONE`.

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

Stato: `IMPLEMENTED_NOT_ACCEPTED`.

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

### GUI-U-E3-T07 — Riscontri operativi delle azioni principali

Stato: `IMPLEMENTED_NOT_ACCEPTED`.
Risultato: ogni azione primaria comunica subito se e` partita e mostra poi un
esito finale comprensibile e azionabile.
Dipendenza: `GUI-U-E3-T06 = DONE`; esito umano negativo di `GATE U-H3` del
2026-07-17.
Componenti ammessi: viste `user_app`, controller Home, coda eventi condivisa,
servizio di verifica casella, proiezione Attivita e test con fake.
Esclusioni: servizi reali, nuove operazioni, modifiche a Limbo, autenticazione
Google, Registro condiviso e packaging.
Condizione di blocco: l'esito non puo` essere esposto senza mostrare output
tecnico o senza distinguere accettazione, avanzamento e completamento.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `Verifica collegamento` mostra avvio, successo o errore azionabile della casella selezionata. | Test UI con connessione lenta, successo e autenticazione rifiutata. | `test_connection_check_shows_immediate_progress_then_success_without_blocking` verifica riscontro immediato e completamento asincrono; `test_connection_authentication_failure_is_actionable_and_redacted` verifica il rifiuto azionabile. | `MET` |
| `Controlla ora` mostra richiesta accettata e riepilogo finale oppure errore. | Test controller/view con eventi di completamento. | `test_check_now_reports_acceptance_and_final_result` distingue richiesta accettata e riepilogo finale con aggiornamento attivita`. | `MET` |
| `Avvia` e `Pausa` aggiornano lo stato visibile e spiegano richieste rifiutate. | Test di ciclo avvio, doppio avvio e pausa. | `test_start_double_start_and_pause_have_visible_coherent_feedback` copre avvio, doppio avvio rifiutato, richiesta di pausa e stato finale. | `MET` |
| La Home consuma periodicamente gli eventi del runner e aggiorna stato, ultimo controllo e Attivita. | Test di polling deterministico senza bloccare la finestra. | `test_home_schedules_periodic_non_blocking_event_consumption` verifica la pianificazione periodica; `test_home_poll_updates_state_last_check_and_activity_count` verifica ora Europe/Rome e conteggio aggiornato; suite e smoke `448 passed`. | `MET` |
| Gli errori installati restano leggibili e non espongono dettagli tecnici o credenziali. | Test su errori sintetici e inventario testi. | `test_runner_error_never_exposes_installed_runtime_details_or_credentials`, test autenticazione e inventario GUI escludono dettagli interni, path e valori sentinella. | `MET` |

### GUI-U-E3-T08 — Limbo, persistenza e interazioni di base

Stato: `IMPLEMENTED_NOT_ACCEPTED`.
Risultato: la scelta del Limbo e` inequivocabile, persistente e utilizzabile con
i normali comandi Windows di selezione e copia/incolla.
Dipendenza: `GUI-U-E3-T07 = DONE`.
Componenti ammessi: wizard, Impostazioni, selettore cartella, binding comuni dei
controlli testuali, configurazione condivisa e test UI.
Esclusioni: scelta della Quarantena, API Drive, modifica del Limbo cloud,
scansione e servizi reali.
Condizione di blocco: il percorso locale sincronizzato non puo` essere distinto
in modo verificabile dalla Quarantena o richiede all'utente dettagli tecnici.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Il wizard definisce il Limbo come cartella locale del Limbo Drive sincronizzato e non come Quarantena. | Test inventario testi e revisione del percorso. | `test_limbo_copy_identifies_the_synced_drive_folder_without_quarantine_fields`: descrizione esplicita del Limbo Drive sincronizzato e inventario privo di Quarantena (`1 passed`). | `MET` |
| Il Limbo si sceglie con un selettore cartella e deve essere una directory assoluta esistente. | Test selettore e validazioni. | `test_folder_selector_and_validator_require_an_existing_absolute_directory`: selezione positiva e rifiuto di percorso relativo o inesistente (`1 passed`). | `MET` |
| Tornando indietro, riaprendo la configurazione o le Impostazioni, il percorso salvato resta valorizzato. | Test round-trip completo. | `test_limbo_value_survives_back_navigation_and_reopening_configuration` e `test_settings_folder_selector_persists_and_reloads_the_limbo` coprono navigazione, riapertura e persistenza (`2 passed`). | `MET` |
| La GUI non chiede di scegliere la Quarantena ne` un URL o ID Drive non necessario al percorso locale. | Test inventario campi visibili. | Inventario mirato T08 e inventario globale stringhe GUI verdi (`3 passed` complessivi); nessun campo Quarantena, URL o ID Drive. | `MET` |
| Campi e messaggi consentono selezione, copia/incolla da tastiera e menu contestuale Windows. | Test binding condivisi sui controlli testuali. | `test_text_controls_offer_keyboard_and_windows_context_menu_actions`: selezione, taglia/copia/incolla e menu destro condivisi verificati (`1 passed`). | `MET` |

### GUI-U-E3-T09 — Accesso alle caselle Google

Stato: `IMPLEMENTED_NOT_ACCEPTED` (implementato il 2026-07-17).
Risultato: Gmail e Google Workspace hanno un percorso di accesso coerente con le
policy Google correnti e distinto dall'IMAP generico.
Dipendenza: `GUI-U-E3-T08 = DONE`.
Componenti ammessi: servizio connessione casella, credenziali Windows, flusso
OAuth Google gia` dichiarato, input protetto della build e test con fake.
Esclusioni: password reali nei test, memorizzazione in chiaro, accesso Google
reale automatico e modifica delle policy di sicurezza.
Decisione umana: `A - solo OAuth`, confermata il 2026-07-17. Per Gmail,
Google Workspace e Drive l'utente apre l'accesso Google dal programma; Caronte
gestisce token e rinnovi senza richiedere progetti Cloud o token manuali.
Condizione di blocco: nessuna per codice e prove sintetiche. Prima del prossimo
collaudo della distribuzione il titolare deve registrare una volta il client
OAuth Desktop di Caronte e passarlo alla build con l'input locale ignorato
documentato in `docs/GOOGLE_OAUTH_DESKTOP.md`.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Gmail/Workspace propone accesso Google e non la password ordinaria dell'account. | Test UI per provider Google. | `test_gmail_view_offers_google_access_without_password_path` verifica vista predefinita senza password e azione `Accedi con Google`; il flusso usa `InstalledAppFlow` Desktop. | `MET` |
| Nessun percorso password per app e` offerto per account Google. | Test testi e assenza del percorso alternativo. | Il validatore accetta Gmail solo con credenziali OAuth strutturate e rifiuta password ordinarie anche se il server viene impostato manualmente a `imap.gmail.com`. | `MET` |
| IMAP generico conserva host, porta e credenziale specifica del provider. | Test regressione provider non Google. | `test_generic_imap_keeps_provider_specific_host_port_and_password` e la regressione CRUD multi-account conservano host, porta e credenziale del provider. | `MET` |
| La verifica distingue accesso riuscito, credenziali rifiutate, rete assente e configurazione incompleta. | Test fake per quattro esiti. | I test OAuth/connessione coprono successo e messaggi distinti per configurazione mancante, consenso rifiutato e rete assente senza dettagli sensibili. | `MET` |
| Token o password restano nel gestore credenziali e non nei file o nei messaggi. | Test persistenza e scansione segreti. | `test_google_credentials_are_persisted_only_in_protected_store` verifica token solo nel `CredentialStore`; configurazione e messaggi ne sono privi. Suite, smoke e scansione segreti verdi. | `MET` |

### GUI-U-E3-T10 — Registro e collegamento Google comprensibili

Stato: `IMPLEMENTED_NOT_ACCEPTED` (implementato il 2026-07-17).
Risultato: l'utente comprende che il Registro e` sempre usato e puo` completare
il collegamento Google richiesto senza conoscere Bucoliche o configurazioni
tecniche.
Dipendenza: `GUI-U-E3-T09 = DONE`.
Componenti ammessi: vista Registro, servizio Bucoliche condiviso rinominato solo
nella presentazione, OAuth browser, selezione guidata del Registro e test fake.
Esclusioni: nuovo registro, modifica degli Apps Script, file o credenziali reali,
esposizione di nomi interni.
Decisione umana acquisita il 2026-07-17: prima versione con Registro scelto
dall'amministratore per ogni installazione. Caronte salva solo l'identificativo
stabile del foglio, non la cartella madre: spostamenti della cartella o del
foglio non richiedono modifiche finche` identificativo e permessi restano validi.
Condizione di blocco residua: nessuna per lo sviluppo locale; per il collaudo
reale resta necessario il client OAuth Desktop centrale gia` previsto in T09.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Il Registro delle attivita` e` sempre attivo e non esiste una scelta utente per disabilitarlo. | Test stato e assenza del toggle. | `test_register_is_always_present_and_reports_administrative_configuration` verde. | `MET` |
| `Bucoliche` e i nomi delle sue schede non compaiono nella GUI utente. | Test inventario testi visibili. | `test_guided_view_shows_clear_steps_and_known_error_messages` verifica testi visibili e assenza del nome interno; controllo stringhe vietate verde. | `MET` |
| `Collega Google` apre un flusso interattivo e identifica chiaramente account e autorizzazione del Registro. | Test OAuth fake e apertura browser controllata. | `test_google_connection_is_a_guided_step_using_only_the_injected_adapter` verde; errore tradotto in azione utente. | `MET` |
| Il Registro condiviso si seleziona o riconosce con un percorso guidato, senza file tecnici o variabili esterne. | Test selezione e persistenza dell'identificativo. | `test_administrator_selection_persists_stable_spreadsheet_id_without_external_variable` verde. | `MET` |
| Verifica e problemi del Registro hanno esiti visibili, specifici e azionabili. | Test successi ed errori sintetici. | Test fake su Registro assente, esito OAuth e verifica read-only verdi. | `MET` |

### GUI-U-E3-T11 — Avvio automatico della distribuzione installata

Stato: `IMPLEMENTED_NOT_ACCEPTED`.
Risultato: Caronte installato puo` avviarsi all'accesso a Windows e controllare
in automatico senza dipendere dal repository o da una runtime esterna.
Dipendenza: `GUI-U-E3-T10 = DONE`.
Componenti ammessi: adapter avvio Windows, supervisore, comando congelato,
Task Scheduler/registro utente e test isolati.
Esclusioni: servizio Windows, privilegi amministrativi, processo permanente
aggiuntivo, GUI legacy.
Condizione di blocco: la build congelata non puo` rappresentare i due comportamenti
senza percorsi di sviluppo o senza lasciare processi orfani.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `Avvia Caronte quando accedo a Windows` registra un comando valido della build installata. | Test registro e avvio da profilo isolato. | `test_windows_startup_adapter_uses_installed_executable_when_frozen` verde; build e `smoke_caronte_build.ps1` avviano `Caronte.exe` dalla sola cartella copiata. | `MET` |
| Il controllo automatico usa l'eseguibile installato senza repository o runtime esterna. | Test piano Task Scheduler congelato. | `test_frozen_watch_task_uses_only_installed_executable` verde: azione con `Caronte.exe watch`, senza modulo o repository. | `MET` |
| Attivazione, stato e rimozione mostrano esiti visibili e coerenti. | Test UI e adapter fake. | `test_automatic_control_install_remove_and_status_use_fake_scheduler` verde: stato, attivazione e rimozione espongono i messaggi utente previsti. | `MET` |
| Disinstallazione rimuove ogni avvio automatico del programma. | Smoke installazione, attivazione e disinstallazione. | `test_uninstall_removes_automatic_startup_before_program_files` verde; `smoke_caronte_installer.ps1` conferma disinstallazione isolata e conservazione dati utente. | `MET` |
| Nessun processo resta orfano dopo pausa, chiusura o disinstallazione. | Test lifecycle e smoke isolato. | `test_unregister_running_windows_task_stops_it_before_deletion` verifica `/end` prima di `/delete`; smoke build e installer verdi. | `MET` |

Il blocco toolchain del 2026-07-17 e` risolto: build e smoke della distribuzione
sono di nuovo disponibili. Tutte le evidenze specifiche sono registrate; il
prossimo task operativo e` `GUI-U-E3-T12`.

### GUI-U-E3-T12 — Chiusura e riduzione a icona comprensibili

Stato: `IMPLEMENTED_NOT_ACCEPTED`.
Risultato: i controlli della finestra distinguono senza ambiguita` riduzione a
icona, ritorno alla Home e chiusura generale.
Dipendenza: `GUI-U-E3-T11 = DONE`.
Componenti ammessi: shell utente, preferenze di chiusura, vista Impostazioni e
test GUI sintetici.
Esclusioni: nuove schermate, tray icon, GUI legacy, modifiche al supervisore.
Condizione di blocco: Windows non espone un comportamento verificabile per
riduzione o chiusura nel profilo isolato.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| La scelta di ridurre a icona alla chiusura salva e viene applicata. | Test preferenza, protocollo finestra e riapertura. | `test_settings_view_saves_preferences_and_updates_close_behavior` e `test_saved_minimize_preference_is_loaded_when_shell_is_reopened` verdi. | `MET` |
| Il comando di chiusura generale e` visivamente distinto dalla navigazione. | Test inventario controlli e revisione sintetica. | `test_window_controls_are_visible_and_close_owned_worker` verde: `Riduci a icona` e `Chiudi Caronte` sono controlli separati. | `MET` |
| Tornare alla Home non arresta Caronte. | Test routing e stato del supervisore fake. | `test_returning_home_keeps_the_owned_worker_running` verde. | `MET` |
| Chiudere esplicitamente arresta il supervisore senza processi residui. | Test lifecycle fake. | `test_window_controls_are_visible_and_close_owned_worker` verde: la chiusura invoca il lifecycle fake e distrugge la finestra. | `MET` |

Test mirati `31 passed`; suite local connector e smoke locale `474 passed`.

### GUI-U-E3-T13 — Attivita` visibili e utili

Stato: `IMPLEMENTED_NOT_ACCEPTED`.
Risultato: i controlli utente producono riscontri consultabili in `Attivita e
problemi`, anche quando non trovano nuovi documenti.
Dipendenza: `GUI-U-E3-T12 = DONE`.
Componenti ammessi: servizi attivita`, controller Home, proiezione eventi e test
sintetici.
Esclusioni: nuove fonti dati, rete reale, modifiche al Registro condiviso.
Condizione di blocco: gli eventi esistenti non permettono di distinguere in modo
sicuro controllo, avvio, pausa e completamento.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `Controlla ora` crea un riscontro leggibile. | Test controller e tabella Attivita`. | `test_home_actions_remain_visible_in_activities_including_an_empty_check`: la richiesta resta nella tabella con testo utente. | `MET` |
| `Avvia` e `Pausa` creano riscontri leggibili e ordinati. | Test eventi lifecycle fake. | Stesso test: riscontri di controllo, completamento e pausa nella sorgente condivisa, in ordine di emissione. | `MET` |
| Un controllo senza documenti mostra comunque il suo esito. | Test completamento sintetico vuoto. | Stesso test con sorgente audit vuota: `Controllo completato` resta consultabile con esito `Riuscito`. | `MET` |
| I dettagli tecnici restano inattivi finche` non esiste una riga selezionabile. | Test vista senza e con eventi. | `test_home_actions_remain_visible_in_activities_including_an_empty_check` e `test_problem_has_recommended_action_and_technical_detail_is_opt_in` verdi: pannello chiuso prima della selezione. | `MET` |

### GUI-U-E3-T14 — Registro e avvio guidati senza finestre tecniche

Stato: `IMPLEMENTED_NOT_ACCEPTED`.
Risultato: `Registro e avvio` resta nella finestra Caronte, espone gli stati
reali del Registro e dell'avvio automatico e indica una sola azione utile.
Dipendenza: `GUI-U-E3-T13 = DONE`.
Componenti ammessi: vista Registro e avvio, servizi applicativi esistenti,
adapter Windows e test fake.
Esclusioni: nuovo OAuth, selezione utente del Registro, shell, GUI legacy.
Condizione di blocco: un esito dell'adapter non e` traducibile senza dettagli
tecnici o richiede configurazioni amministrative non disponibili.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Nessuna azione Registro o avvio apre una finestra di shell. | Test adapter e avvio GUI isolato. | `test_scheduler_queries_run_without_a_console_window` verifica `CREATE_NO_WINDOW`; `test_guided_view_offers_one_automatic_control_action_at_a_time` usa la vista isolata con adapter fake. | `MET` |
| Registro non configurato mostra stato e unica azione comprensibili. | Test fake configurazione assente. | `test_register_is_always_present_and_reports_administrative_configuration` verifica stato, richiesta all'amministratore e nessun avvio del collegamento Google. | `MET` |
| Collegamento Google non configurato mostra un esito guidato senza dettagli interni. | Test fake OAuth non disponibile. | `test_google_configuration_problem_has_a_guided_message` verifica l'indicazione all'amministratore e l'assenza di termini tecnici. | `MET` |
| Stato e attivazione dell'avvio automatico mostrano esiti coerenti. | Test adapter fake successo e errore. | `test_automatic_control_install_remove_and_status_use_fake_scheduler` e `test_guided_view_offers_one_automatic_control_action_at_a_time` verificano stato, attivazione e disattivazione con una sola azione alla volta. | `MET` |

### GATE U-H3 — Collaudo umano di distribuzione

Stato: `DONE`.

Codex non puo` dichiararlo `PASS`.

Prerequisiti verificati: `GUI-U-E3-T01` - `GUI-U-E3-T06 = DONE`; test mirati
installer `9 passed`, suite local connector `442 passed`, smoke locale
`442 passed` e smoke installer isolato completato con dati sintetici preservati.

Esito umano del 2026-07-17: `FAIL`. Installazione, collegamento Start,
conclusione del wizard, persistenza e disinstallazione sono riusciti. Il collaudo
ha rilevato assenza di riscontri osservabili per verifica casella, controllo,
avvio e pausa; significato ambiguo e mancata persistenza del Limbo tornando
indietro; accesso Gmail non guidato; `Bucoliche` e collegamento Google non
comprensibili ne` completabili; avvio automatico non attivabile; copia/incolla e
selezione testo incomplete. I task `GUI-U-E3-T07` - `GUI-U-E3-T14` devono essere
`DONE` prima di ripetere il gate.

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

Esito umano del 2026-07-20: `FAIL`. Non e` stato osservato alcun miglioramento
concreto rispetto alle osservazioni gia` riportate: nessuna correzione e` stata
validata nel percorso percepito dall'utente. L'EPIC GUI-U resta `BLOCKED`; non
sono autorizzati nuovi correttivi autonomi finche` non viene definito un nuovo
piano di recupero con scenari osservabili e criteri di accettazione umani.

## GUI-U-R - Recupero prodotto e collaudo osservabile

Stato iniziativa: `GUI-U = RECOVERY_ACTIVE`.

La classificazione `IMPLEMENTED_NOT_ACCEPTED` di `GUI-U-E3-T07` - `T14`
significa che il codice e` implementato e i test sintetici sono superati, ma il
risultato non e` stato accettato dal collaudo umano. Non e` dimostrato che
l'installer collaudato corrispondesse alla sorgente piu recente; i test
esistenti non sono evidenza sufficiente di qualita UX. Non sono autorizzati
microcorrettivi prima del nuovo prototipo visuale.

### GUI-U-R01 - Identita certa della build e dell'installer

Stato: `DONE`.
Risultato: eseguibile e installer dichiarano e verificano la sorgente precisa da
cui sono stati prodotti, impedendo un collaudo inconsapevole di una vecchia build.
Dipendenze: secondo `GATE U-H3 = FAIL` registrato il 2026-07-20.
Componenti ammessi: build-info, entry point, finestra Informazioni, spec e script
di build/installer, smoke, test mirati e documentazione di collaudo.
Esclusioni: layout operativo, nuove schermate operative, account, Limbo, OAuth,
Registro, pipeline, servizi reali e nuovi toolkit.
Condizione di blocco: toolchain Windows non produce nella stessa esecuzione una
build pulita, un installer identificato e smoke coerenti con il commit corrente.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R01-AC1` Manifest interno completo e build di collaudo rifiutata se dirty, senza commit o su branch diversa. | Test manifest e ispezione script; build pulita reale. | Test mirati verificano schema e invalidi; script acquisisce Git/Python/PyInstaller/build ID e applica i tre gate. | `MET` |
| `R01-AC2` Informazioni mostra solo versione, commit breve, data e build ID. | Test sulla proiezione visibile e disponibilita nella build. | Modulo Informazioni usa la stessa identita validata e non espone ambiente o percorsi. | `MET` |
| `R01-AC3` `Caronte.exe --build-info` non apre la GUI, coincide con Informazioni e fallisce senza manifest valido. | Test entry point e smoke della build. | Test coprono successo, coincidenza e errore; smoke confronta i quattro campi. | `MET` |
| `R01-AC4` Installer `CaronteSetup-<version>-<short-sha>.exe`, stessa build e versione registrata, senza riuso di `dist`. | Test script/installer e smoke isolato. | La pipeline ricostruisce la build, pulisce output, deriva il nome dal manifest e verifica `DisplayVersion`. | `MET` |
| `R01-AC5` Manifest release esterno completo accanto all'installer. | Test struttura script e verifica artefatto reale. | Lo script registra nome, dimensione, SHA-256, identita, stato clean, tre esiti e comando sanificato. | `MET` |
| `R01-AC6` Smoke installer confronta sorgente, apre Caronte, verifica Informazioni e disinstalla. | Smoke su profilo cartelle/registro isolato. | Lo smoke confronta versione, commit e build ID, controlla nome/versione, finestra e modulo Informazioni, poi disinstalla preservando dati sintetici. | `MET` |

### GUI-U-R02 - Prototipo visuale completo

Stato: `SUPERSEDED_BY_R3`.
Risultato: prototipo completo delle cinque schermate con dati sintetici ed
evidenze prodotte dalla build installata reale.
Esito umano del 2026-07-23: `FAIL`. In installazione pulita la schermata
Caselle non permette di inserire le caselle demo e blocca il passaggio al
Riepilogo; la build presenta quindi il percorso ordinario non configurato,
anziche` un percorso demo eseguibile senza Google. Il pulsante osservato e`
`Termina configurazione`, non `Completa configurazione` come da criterio.
Codex non puo dichiarare `PASS`. Il `FAIL` resta evidenza storica del demo; non
e` un'autorizzazione a eliminare i requisiti UX osservati.

La sotto-epica e` suddivisa per separare il percorso dimostrativo, la resa delle
schermate e le prove sulla build installata. Nessun task collega servizi reali.

#### GUI-U-R02-T01 - Percorso dimostrativo isolato

Stato: `IMPLEMENTED_NOT_ACCEPTED`.
Risultato: Caronte offre un percorso dimostrativo ripetibile, con dati sintetici,
attraverso Benvenuto, Limbo, Caselle, Riepilogo e Home.
Dipendenza: `GUI-U-R01 = DONE`.
Componenti ammessi: stato demo in memoria, navigazione `user_app`, viste gia`
esistenti, test GUI mirati e documentazione minima.
Esclusioni: servizi reali, persistenza reale, credenziali, OAuth, Registro,
build/installer, redesign visuale delle schermate, nuove dipendenze e GUI legacy.
Condizione di blocco: non e` possibile isolare i dati sintetici dalla
configurazione e dalle credenziali locali senza cambiare i contratti condivisi.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R02-T01-AC1` Il percorso demo parte senza configurazione o credenziali locali. | Test con filesystem e credential store finti. | `test_demo_route_uses_only_synthetic_state_and_reaches_all_five_screens`: store configurazione che fallisce se interrogato, percorso avviato. | `MET` |
| `R02-T01-AC2` Le cinque schermate sono raggiungibili nel solo percorso Benvenuto -> Limbo -> Caselle -> Riepilogo -> Home. | Test di routing con shell Tk finta. | Stesso test: cinque passi e route Home finale; test GUI mirati `22 passed`. | `MET` |
| `R02-T01-AC3` Limbo e due caselle sintetiche restano coerenti dopo Indietro/Continua. | Test di navigazione e stato in memoria. | Stesso test: due caselle demo, ritorno da Riepilogo a Caselle e nuovo avanzamento. | `MET` |
| `R02-T01-AC4` Il percorso demo non esegue rete, salvataggi reali o accessi a credenziali. | Test con adapter che falliscono a ogni accesso esterno. | Store di configurazione esplosivo non viene letto/scritto; `DemoHomeControl` non avvia operazioni. | `MET` |
| `R02-T01-AC5` Le stringhe vietate non sono visibili nel percorso demo. | Test automatico sull'inventario delle stringhe visuali. | Inventari automatici GUI `test_user_app.py` e verticale verdi; verifica mirata dei testi demo inclusa. | `MET` |

Riscontro umano 2026-07-23: `FAIL` su installazione pulita. Dopo Limbo, Caselle
non consente di aggiungere alcuna casella e il percorso non puo` raggiungere
Riepilogo/Home. Il comportamento richiede o sembra richiedere una
configurazione Google, esclusa esplicitamente da R02; non e` stata fornita
evidenza screenshot. Questa e` una regressione riproducibile contro
`R02-T01-AC1`-`AC3`, non un limite atteso del collaudo.

#### GUI-U-R02-T02 - Schermate del primo avvio osservabili

Stato: `DONE`.
Risultato: Benvenuto, Limbo, Caselle e Riepilogo presentano una gerarchia visuale
leggibile e azioni coerenti con gli scenari `H-R02-01`-`H-R02-05`.
Dipendenza: `GUI-U-R02-T01 = DONE`.
Componenti ammessi: viste `user_app` del primo avvio, risorse locali, test GUI e
documentazione minima.
Esclusioni: Home, servizi reali, persistenza reale, build/installer, GUI legacy e nuove dipendenze.
Condizione di blocco: la resa non puo` restare leggibile a 960x640 e con scala
Windows 100%/125% usando il toolkit e le risorse locali approvate.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R02-T02-AC1` Benvenuto rende immediati identita`, scopo e azione iniziale. | Test delle label/azioni e screenshot locale controllato. | Test reale Tk verifica titolo, scopo e azione `Inizia la configurazione`; prova automatica verde a 960x640 e 100%/125%. | `MET` |
| `R02-T02-AC2` Limbo mostra istruzione, selettore, valore ed errore presso il campo. | Test UI e screenshot locale controllato. | Test reale Tk verifica istruzione, etichetta del campo e selettore; i test mirati della validazione locale sono verdi. | `MET` |
| `R02-T02-AC3` Caselle separa elenco e form, rende evidente la seconda casella e relega i campi avanzati. | Test UI e screenshot locale controllato. | Elenco/form, invito alla seconda casella e pannello avanzato chiuso sono verificati dai test GUI; resa reale Tk verde. | `MET` |
| `R02-T02-AC4` Riepilogo mostra completezza e una correzione azionabile per ogni dato mancante. | Test UI e screenshot locale controllato. | Riepilogo espone Limbo, numero caselle e ritorno `Indietro` per la correzione; test reale Tk verde. | `MET` |
| `R02-T02-AC5` Le quattro schermate restano utilizzabili a 960x640 e nei test di resize. | Test geometria/resize con Tk e ispezione screenshot. | Nuovo test con Tk reale percorre le quattro viste a 960x640 e scala 100%/125%; la regressione iniziale Caselle `760 px` e` corretta e tutte le altezze sono `<=640`. | `MET` |

Evidenze di chiusura: runtime Python Windows ripristinato con Tcl/Tk `8.6.15`;
test mirati GUI `31 passed`, suite locale e smoke `489 passed`; inventario
automatico delle stringhe visuali, diff e scansione segreti verdi.

#### GUI-U-R02-T03 - Home dimostrativa ed evidenze installate

Stato: `IMPLEMENTED_NOT_ACCEPTED`.
Risultato: Home dimostrativa coerente con il percorso e pacchetto di evidenze
reali della build installata, pronto per il collaudo umano R02.
Dipendenza: `GUI-U-R02-T02 = DONE`.
Componenti ammessi: Home `user_app`, dati demo, pipeline di build/installer gia`
approvata, smoke e artefatti di collaudo.
Esclusioni: servizi reali, credenziali, modifiche ai contratti applicativi,
nuovi toolkit e GUI legacy.
Condizione di blocco: non e` possibile produrre o installare una build identificata
del commit corrente, oppure non e` possibile acquisire le evidenze reali richieste.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R02-T03-AC1` Home mostra stato, caselle, prossima azione, attivita`, problemi e azione primaria con dati demo. | Test UI e screenshot locale controllato. | `test_demo_home_makes_status_next_action_activity_and_problems_visible`; Home installata in `home-100.png` e `home-125.png`. | `MET` |
| `R02-T03-AC2` Home e primo avvio hanno gerarchia leggibile nei resize minimi previsti. | Test geometria/resize e screenshot locale controllato. | Test Tk reale unico percorre le cinque viste a 960x640 e scala `1.0`/`1.25`; `491 passed` nello smoke locale. | `MET` |
| `R02-T03-AC3` Build e installer del commit corrente superano gli smoke di identita` e installazione. | Build pulita, smoke build e smoke installer isolato. | Release `4cbcea4`, build ID `f7eb037d-924e-4a04-b9a9-3f2751137a42`; `release_manifest.json` registra build, smoke build e smoke installer `PASS`. | `MET` |
| `R02-T03-AC4` La cartella `artifacts/gui-u-r02/<build-id>/` contiene manifest, hash, cinque screenshot reali, varianti scala e checklist/instructions. | Verifica struttura e apertura manuale degli artefatti. | Cartella ignorata `artifacts/gui-u-r02/f7eb037d-924e-4a04-b9a9-3f2751137a42/`: due manifest, SHA-256, cinque screenshot diretti dell'eseguibile installato a `100`/`125`, checklist e istruzioni; Home aperta e verificata. | `MET` |
| `R02-T03-AC5` La scheda R02 e il collaudo umano sono preparati come `WAITING_HUMAN_REVIEW`, senza dichiarare `PASS`. | Revisione documentale e stato Git. | Questa sotto-epica e T03 sono `WAITING_HUMAN_REVIEW`; checklist vuota copiata nel fascicolo; `docs/GUI_U_HUMAN_ACCEPTANCE.md` resta l'unico riferimento umano. | `MET` |

Riscontro umano 2026-07-23: non valutabile nella build installata, perche` il
blocco Caselle impedisce di raggiungere Home dal percorso iniziale. Il criterio
di etichetta del Riepilogo osservabile richiede inoltre `Completa
configurazione`, mentre nella build e` stato osservato `Termina configurazione`.

Decisione utente del 2026-07-23, chiarita nella stessa data: bypassare il demo,
non i requisiti R2. Il demo resta solo uno strumento interno di evidenza e non
viene ampliato, corretto o ricollaudato. Gli scenari `H-R02-01`--`H-R02-08`
sono trasferiti integralmente a R3 e devono risultare soddisfatti sul percorso
operativo reale prima del suo unico collaudo umano.

### GUI-U-R03 - Collegamento dei servizi

Stato: `FAIL`.
Risultato: il prototipo visuale approvato usa i servizi applicativi condivisi
per Limbo, due caselle, controlli operativi, persistenza e controllo automatico,
con riscontri osservabili nella GUI e senza esporre dettagli tecnici.
Dipendenza: decisione utente del 2026-07-23 di privilegiare il percorso
operativo reale e limitare i dati demo al minimo indispensabile; eredita senza
eccezioni i requisiti UX R2.
Componenti ammessi: viste `user_app` approvate in R02, servizi applicativi
condivisi di configurazione, account, credenziali, verifica read-only, runner,
attivita`, impostazioni e adapter Windows; test automatici con fake; evidenze e
checklist di collaudo R03.
Esclusioni: redesign del layout approvato, GUI legacy, nuovi toolkit, duplicazione
della logica CLI, modifiche ad Apps Script, Registro o pipeline non necessarie
ai sei scenari R03, credenziali o servizi reali nei test automatici.
Condizione di blocco: un servizio richiesto non puo` essere collegato alle viste
senza esporre termini tecnici, bloccare la GUI o richiedere una nuova dipendenza
strutturale.

Matrice vincolante di trasferimento R2 -> R3:

| Requisito R2 | Destinazione di sviluppo | Condizione di chiusura |
| ------------ | ------------------------ | ---------------------- |
| `H-R02-01` Avvio e orientamento | `R03-T03` | Dimostrato sul primo avvio reale in una sola finestra. |
| `H-R02-02` Navigazione wizard | `R03-T03` | Benvenuto -> Limbo -> Caselle -> Riepilogo -> Home conserva i dati reali. |
| `H-R02-03` Limbo | `R03-T03`, `R03-AC1` | Selezione, errore locale, salvataggio, modifica e persistenza reali. |
| `H-R02-04` Caselle | `R03-T01`, `R03-T02`, `R03-AC2` | Prima e seconda casella, Google/IMAP, stati e campi avanzati funzionano realmente. |
| `H-R02-05` Riepilogo | `R03-T03` | Riepilogo reale autonomo con correzioni e `Completa configurazione`. |
| `H-R02-06` Home | `R03-T03`, `R03-AC3`--`R03-AC5` | Stato, azioni, attivita`, problemi e Impostazioni riflettono i servizi reali. |
| `H-R02-07` Leggibilita | Tutti i task R3 che cambiano viste; gate R3 | Nessun taglio a 960x640 e scala 100%/125% sulla build operativa. |
| `H-R02-08` Linguaggio | Tutti i task R3 che cambiano testi; gate R3 | Nessun termine tecnico vietato; errori con problema e azione. |

Questa matrice e` un prerequisito del gate R3. Un requisito puo` riusare
un'evidenza gia` valida, ma deve essere nuovamente provato solo quando il
passaggio dal demo al servizio reale ne cambia il comportamento osservabile.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R03-AC1` Il Limbo reale si seleziona, valida, salva, persiste dopo riapertura e si modifica da Impostazioni (`H-R03-01`). | Test applicativi/UI con filesystem temporaneo; collaudo umano completo del round-trip. | `H-R03-01 = PASS` umano esplicito il 2026-07-24 sulla build R03-R04: selezione, validazione, salvataggio, ritorno, riapertura, persistenza e modifica da Impostazioni approvati. La larghezza insufficiente dei campi cartella e` registrata come osservazione separata non bloccante. | `MET` |
| `R03-AC2` Prima e seconda casella hanno credenziali distinte, percorsi Google/IMAP corretti e operazioni persistenti di aggiunta, modifica, stato e rimozione (`H-R03-02`, `H-R03-03`). | Test con OAuth/IMAP/credential store fake; collaudo umano su due caselle reali autorizzate. | `H-R03-02` e `H-R03-03 = PASS` umano esplicito il 2026-07-24 sulla build `8241325`, ID `7dcae8b2-5bd2-47b6-9c89-f53b4cf4c1ff`. Test fake mirati gia` verdi; i due `FAIL` precedenti restano storici. | `MET` |
| `R03-AC3` La verifica casella integrata nel collegamento, Controlla ora, Avvia e Pausa mostrano avvio, stato, esito o errore azionabile e registrano l'attivita (`H-R03-04`). | Test asincroni deterministici su successo/errore; collaudo umano delle azioni operative. | `H-R03-04 = PASS` umano esplicito il 2026-07-24 sulla build `8241325`, ID `7dcae8b2-5bd2-47b6-9c89-f53b4cf4c1ff`. Tre screenshot mostrano controllo in corso, ultimo controllo aggiornato, avvio periodico, pausa riuscita e righe coerenti in Attivita. La verifica casella non e` piu` un comando separato: e` gia` coperta dai flussi approvati `H-R03-02`/`H-R03-03`. Test asincroni fake gia` verdi. | `MET` |
| `R03-AC4` Chiusura, eventuale riduzione a icona e riapertura non lasciano console o processi duplicati e conservano configurazione e stato (`H-R03-05`). | Test lifecycle/processi su build installata; collaudo umano di chiusura e riapertura. | `H-R03-05 = PASS` umano esplicito il 2026-07-24 sulla build `8241325`, ID `7dcae8b2-5bd2-47b6-9c89-f53b4cf4c1ff`. Test lifecycle/processi e smoke della build gia` verdi. | `MET` |
| `R03-AC5` Il controllo automatico si attiva, conferma, espone lo stato, persiste e si disattiva senza finestre tecniche (`H-R03-06`). | Test adapter Windows isolato e persistenza; collaudo umano sulla build installata. | `H-R03-06 = PASS` umano esplicito il 2026-07-24 sulla build `eaf05fd`, ID `0c40a31d-ee7a-4d8c-9f0d-5ff795fb5b39`: attivazione senza UAC o finestre tecniche, stato e pulsante corretti, persistenza dopo riapertura e nuovo accesso Windows, disattivazione persistita. Il `FAIL` sulla build `8241325` resta storico. | `MET` |

Esito umano del 2026-07-24: `FAIL` su `H-R03-02`; scenario, passaggio, atteso,
osservato e screenshot sono registrati nel fascicolo ignorato R03. Correttivo
finito proposto, non ancora approvato: `GUI-U-R03-R01 - Verifica collegamento
su INBOX`. La verifica di connettivita` deve selezionare esplicitamente la
cartella standard `INBOX`, restare read-only e non dipendere da cartelle
operative nascoste. Dopo approvazione, test mirati e nuova build identificata,
il collaudo riprende senza ripetere le evidenze gia` valide.

Ripresa del 2026-07-24 sulla build `bb9b16e`: Build ID e installer identificati
correttamente; OAuth e verifica read-only su `INBOX` riescono. `H-R03-02`
resta `FAIL` perche` la casella non viene aggiunta. La GUI presenta inoltre il
limite di 25 messaggi come conteggio visibile e separa in modo poco chiaro
autorizzazione, verifica e aggiunta. Collaudo interrotto; nessuna correzione
applicata durante il gate.

Nuova build R03-R03 pronta per la sola ripresa umana di `H-R03-02`:
`CaronteSetup-0.11.0-8241325.exe`, commit
`8241325bf96d858259a577c87ffaba8c25513a05`, Build ID
`7dcae8b2-5bd2-47b6-9c89-f53b4cf4c1ff`, SHA-256
`79BC5677B21B29CAF3F7E07A9394072FBBBA446DA573FF5AF0181B8CFF260FF8`.
Il client OAuth Desktop e` incorporato; smoke build e installer sono `PASS`.
Conferme umane esplicite del 2026-07-24: `H-R03-02 = PASS` e
`H-R03-03 = PASS`. `R03-AC2 = MET`. La prosecuzione ha confermato
`H-R03-04 = PASS` con tre screenshot; `R03-AC3 = MET` e il collaudo prosegue
con `H-R03-05 = PASS`; `R03-AC4 = MET`. `H-R03-06 = FAIL` per mancata
creazione dell'avvio automatico Windows; il gate e` interrotto.

Ripresa del 2026-07-24 sulla build R03-R04 `eaf05fd`, ID
`0c40a31d-ee7a-4d8c-9f0d-5ff795fb5b39`: `H-R03-06 = PASS` umano e
`R03-AC5 = MET`. La successiva conferma esplicita `H-R03-01 = PASS` porta
`R03-AC1 = MET` e chiude `GUI-U-R03 = DONE`.

#### GUI-U-R03-R01 - Verifica collegamento su INBOX

Stato: `DONE` (approvato e completato il 2026-07-24).
Risultato: `Accedi con Google` e `Verifica collegamento` dimostrano accesso,
autenticazione e lettura IMAP usando la cartella standard `INBOX`, senza
dipendere dalla cartella operativa configurata per acquisire i documenti.
Dipendenza: `GUI-U-R03 = FAIL` su `H-R03-02`; diagnosi reale con OAuth e IMAP
read-only completata.
Componenti ammessi: `AccountConnectionRequest`,
`ReadonlyAccountConnectionService`, test fake mirati e documentazione minima.
Esclusioni: rete o credenziali reali nei test, campi GUI, cartelle operative,
redesign, Apps Script, Registro, pipeline e nuove dipendenze.
Condizione di blocco: la verifica non puo` selezionare `INBOX` in sola lettura
oppure la correzione modifica la cartella usata dalle operazioni reali.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R03-R01-AC1` La richiesta di verifica dichiara `INBOX` e il servizio la passa all'adapter IMAP read-only. | Test unitario su configurazione ricevuta dal mailbox fake. | `AccountConnectionRequest.mailbox` vale `INBOX` e `ReadonlyAccountConnectionService` lo trasferisce esplicitamente a `ImapReadonlyConfig`. | `MET` |
| `R03-R01-AC2` Il caso riprodotto, in cui manca `Virgilio/da-traghettare` ma `INBOX` e` disponibile, completa la verifica. | Regressione fake che accetta soltanto `INBOX`. | `test_connection_check_uses_standard_inbox_not_operational_default` era rosso sul default operativo ed e` verde dopo il correttivo. | `MET` |
| `R03-R01-AC3` Le sole prove R03-T02 restano verdi senza rete o credenziali reali. | `test_account_connection.py`, `test_user_app_accounts.py` e `test_user_app_operational_feedback.py`. | Gruppo mirato `15 passed in 0.69s`, con fake e basetemp isolato; nessuna rete o credenziale reale. | `MET` |

Nota fuori ambito confermata dall'utente: la cartella operativa reale e`
`da-traghettare`, senza cartella madre, mentre `AccountManagementService`
assegna oggi `Virgilio_Inbox`, `Virgilio_Done` e `Virgilio_Errori`. Proposto
`GUI-U-R03-R02 - Cartelle operative configurabili per casella`, da approvare
prima di una nuova build, senza reintrodurre file tecnici nella GUI.

#### GUI-U-R03-R02 - Cartelle operative configurabili per casella

Stato: `DONE` (approvato e completato il 2026-07-24).
Risultato: l'utente imposta per ogni casella le cartelle da controllare,
completati e problemi nelle impostazioni avanzate, senza modificare YAML/.env e
senza confonderle con `INBOX`, usata soltanto per verificare il collegamento.
Dipendenza: `GUI-U-R03-R01 = DONE`; conferma umana che la cartella reale e`
`da-traghettare` senza cartella madre.
Componenti ammessi: `AccountForm`, vista Caselle, validatore,
`AccountManagementService`, persistenza esistente e test fake mirati.
Esclusioni: rete o credenziali reali nei test, elenco remoto cartelle, redesign,
Apps Script, Registro, pipeline, nuova build e nuove dipendenze.
Condizione di blocco: i valori non possono restare distinti per casella oppure
la correzione altera il check read-only su `INBOX`.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R03-R02-AC1` Le impostazioni avanzate mostrano `Cartella da controllare`, `Cartella completati` e `Cartella problemi`, senza termini tecnici. | Test vista e inventario testi. | `test_operational_folders_are_advanced_validated_and_persist_per_account` verifica i tre testi nel pannello avanzato; inventario termini vietati verde. | `MET` |
| `R03-R02-AC2` I tre valori sono obbligatori e accettano nomi senza cartella madre, incluso `da-traghettare`. | Test validatore con valore vuoto e caso reale. | `test_operational_folders_are_required` rifiuta il vuoto; il test round-trip salva `da-traghettare`, `traghettate` ed `errore` senza prefisso. | `MET` |
| `R03-R02-AC3` Aggiunta, modifica e riapertura conservano tre valori distinti per ciascuna casella. | Test controller/servizio con due account e filesystem temporaneo. | Il test round-trip aggiunge due terne distinte, ricarica la prima nella vista, modifica `Cartella completati` e ritrova i valori con un nuovo servizio. | `MET` |
| `R03-R02-AC4` `Verifica collegamento` continua a usare `INBOX` e non una cartella operativa. | Regressione R03-R01. | `test_connection_check_uses_standard_inbox_not_operational_default` verde nel gruppo mirato. | `MET` |
| `R03-R02-AC5` Le sole prove interessate R03-R02/R03-T02 sono verdi con fake. | Test account service/UI, connection e feedback asincrono. | Core mirato `17 passed in 1.08s`; sola prova Tk interessata `1 passed in 2.11s`, pannello avanzato entro 960x640 a 100%/125%. | `MET` |

#### GUI-U-R03-R03 - Collegamento casella guidato e salvataggio recuperabile

Stato: `DONE` (approvato e completato il 2026-07-24).
Risultato: ogni provider ha una singola azione comprensibile che verifica e
salva la casella; il percorso Google completa browser, verifica e inserimento
nell'elenco senza un secondo pulsante ambiguo.
Dipendenze: `GUI-U-R03-R01/R02 = DONE`; secondo `FAIL` umano `H-R03-02` e
diagnosi read-only dei riferimenti protetti residui.
Componenti ammessi: vista Caselle, controller, `AccountManagementService`,
servizio credenziali Windows, feedback sicuro, test fake/Tk mirati.
Esclusioni: rete o credenziali reali nei test, nuove dipendenze, redesign delle
altre schermate, Apps Script, Registro, pipeline e nuova build.
Condizione di blocco: il salvataggio non puo` essere reso atomico e
recuperabile senza esporre o perdere credenziali di altre caselle.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R03-R03-AC1` Google espone una sola azione che autorizza, verifica e salva; al successo la riga appare con stato chiaro. | Test controller end-to-end con OAuth, IMAP e persistenza fake. | `test_google_single_action_verifies_adds_and_protects_credentials` completa il percorso con `Collega con Google`, salva nel deposito protetto, mostra la riga e rimuove `Aggiungi casella`. | `MET` |
| `R03-R03-AC2` IMAP espone `Verifica e aggiungi` con lo stesso esito osservabile e senza azioni duplicate. | Test vista/controller per provider generico. | `test_generic_imap_single_action_verifies_and_adds_account` verifica pulsante, check asincrono, salvataggio e riga nell'elenco. | `MET` |
| `R03-R03-AC3` Riferimenti protetti residui senza configurazione vengono riconciliati in modo atomico; ogni errore lascia stato coerente e mostra problema e azione. | Regressioni su credenziali preesistenti, rollback e messaggio sicuro. | Le regressioni riproducono i due riferimenti reali residui, preservano un'altra casella, ripristinano i valori precedenti se il salvataggio configurazione fallisce e oscurano dettagli dell'eccezione. | `MET` |
| `R03-R03-AC4` La verifica comunica soltanto che Caronte puo` leggere la casella oppure dichiara esplicitamente che 25 e` un campione, mai il totale. | Test servizio/testi visibili. | `ReadonlyAccountConnectionService` continua la lettura limitata ma restituisce soltanto `Collegamento riuscito. Caronte può leggere la casella.`; test con zero e due messaggi verdi. | `MET` |
| `R03-R03-AC5` Il flusso resta leggibile a 960x640, 100%/125%, e non introduce termini tecnici o segreti. | Prova Tk interessata e inventario stringhe. | Core mirato finale `37 passed in 0.94s`; sola prova Tk interessata `1 passed in 1.06s`, entro 960x640 a 100%/125%; smoke locale finale `501 passed`; inventario e controlli di non esposizione verdi. | `MET` |

#### GUI-U-R03-R04 - Controllo automatico per utente

Stato: `DONE` (avvio approvato esplicitamente dall'utente e completato il
2026-07-24).
Risultato: il controllo automatico si registra e si rimuove dalla build
installata per il solo utente corrente, senza UAC o privilegi amministrativi e
senza dipendere dalla configurazione del Registro.
Dipendenze: `H-R03-06 = FAIL`; `R03-AC2`--`R03-AC4 = MET`.
Componenti ammessi: servizio condiviso di avvio Windows, gateway del controllo
automatico, vista `Registro e avvio`, pulizia dell'installer/disinstallatore,
test fake/Windows isolati e documentazione minima.
Esclusioni: configurazione reale del Registro, Apps Script, credenziali reali,
elevazione/UAC, nuove dipendenze, redesign delle altre viste e GUI legacy.
Condizione di blocco: il worker congelato non puo` essere avviato e rimosso
tramite una registrazione per-utente senza repository, Python esterno o
privilegi amministrativi.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R03-R04-AC1` Registro e controllo automatico restano indipendenti: Registro assente non blocca ne` spiega l'avvio Windows. | Test servizio/vista con Registro assente e gateway automatico disponibile. | `test_register_is_always_present_and_reports_administrative_configuration` verifica Registro assente, stato automatico leggibile e attivazione riuscita prima di ogni collegamento Google. | `MET` |
| `R03-R04-AC2` Attiva/Disattiva usa una registrazione del solo utente corrente e non richiede Task Scheduler, UAC o amministratore. | Test adapter Windows iniettato e ispezione del comando registrato. | `WindowsAutomaticControlAdapter` usa solo `HKEY_CURRENT_USER\...\Run`; il test iniettato verifica aggiunta/rimozione e assenza di `schtasks`. | `MET` |
| `R03-R04-AC3` La registrazione avvia `Caronte.exe watch` con configurazione e intervallo installati, senza repository o Python esterno. | Test frozen sul comando e smoke da cartella copiata. | Il test frozen verifica eseguibile copiato, `watch`, configurazione e intervallo senza modulo/Python; lo smoke build avvia anche `watch --help` dalla copia isolata. | `MET` |
| `R03-R04-AC4` Stato, attivazione, persistenza, rimozione ed errori sono veritieri e azionabili senza dettagli tecnici. | Test servizio/UI su successo, errore e riapertura. | Stato confrontato con il comando atteso, registrazione obsoleta dichiarata inattiva, attiva/disattiva e riapertura fake verdi; i messaggi restano guidati e non tecnici. | `MET` |
| `R03-R04-AC5` Disinstallazione rimuove la registrazione automatica e test mirati, smoke locale e nuova build identificata sono verdi. | Test installer/disinstallazione, smoke e manifest build. | Pulizia dei due valori `Run` e del task legacy verificata; gruppo mirato `27 passed`, smoke locale `504 passed`; build e installer identificati dal commit conclusivo con smoke `PASS`. | `MET` |

#### GUI-U-R03-R05 - Campi cartella leggibili

Stato: `DONE` (approvato e completato il 2026-07-24).
Risultato: i campi che mostrano percorsi o nomi di cartelle usano lo spazio
orizzontale disponibile e permettono di leggere una parte utile del valore
senza comprimere etichette, selettori o azioni.
Dipendenze: osservazione umana non bloccante acquisita con
`H-R03-01 = PASS`; layout R03 approvato.
Componenti ammessi: campo Limbo del primo avvio, campo Limbo di Impostazioni,
tre campi cartelle operative avanzate delle caselle, pesi/minimi delle colonne
dei rispettivi contenitori e test fake/Tk mirati.
Esclusioni: ridisegno delle viste, modifica della dimensione minima della
finestra, campi non relativi a cartelle, logica di persistenza, servizi,
Apps Script e GUI legacy.
Condizione di blocco: a 960x640 e scala 100%/125% non e` possibile garantire
la larghezza minima senza rendere inaccessibili etichette, pulsanti o azioni.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R03-R05-AC1` Il campo Limbo del primo avvio occupa lo spazio disponibile e mostra almeno 48 caratteri a 960x640. | Test Tk a 100%/125% con percorso sintetico lungo e misura del campo. | `FOLDER_ENTRY_WIDTH = 48`, colonna Limbo elastica; test fake e Tk verificano misura, 960x640 e scale 100%/125%. | `MET` |
| `R03-R05-AC2` Il campo Limbo di Impostazioni rispetta la stessa larghezza e il selettore resta interamente visibile. | Test Tk della vista a 960x640 e 100%/125%. | Stessa larghezza condivisa e colonna del valore elastica; la vista completa, incluso `Scegli cartella...`, resta entro 960x640 alle due scale. | `MET` |
| `R03-R05-AC3` I tre campi cartella avanzati delle caselle si espandono in modo uniforme senza comprimere etichette o azioni. | Test fake del layout e prova Tk delle impostazioni avanzate. | I tre campi condividono larghezza 48 e la sola colonna valori avanzati e` elastica; etichette e azioni restano entro 960x640 a 100%/125%. | `MET` |
| `R03-R05-AC4` Se il valore supera lo spazio, selezione, scorrimento orizzontale, copia e incolla restano disponibili senza tagli verticali. | Test interazioni su valori sintetici lunghi e inventario visuale. | Test Tk con percorso sintetico lungo conferma scorrimento orizzontale; regressione delle interazioni conferma selezione, copia e incolla. Gruppo mirato `47 passed`, smoke locale `506 passed`. | `MET` |

#### GUI-U-R03-T01 - Prima casella reale senza blocco Google

Stato: `DONE`.
Risultato: da installazione pulita l'utente puo` distinguere Google da un'altra
casella IMAP, aggiungere e salvare una prima casella IMAP reale anche quando
Google non e` stato predisposto, quindi terminare la configurazione e riaprire
la casella salvata.
Dipendenza: decisione utente del 2026-07-23; servizi esistenti di configurazione,
gestione caselle e credenziali locali.
Componenti ammessi: vista Caselle, controller del primo avvio, servizi
`AccountManagementService` e credenziali locali, test fake e documentazione
minima.
Esclusioni: dati demo come sostituto di una casella reale, connessioni Google
reali nei test, OAuth nuovo, rete nei test, GUI legacy, Registro, Apps Script,
pipeline e nuove dipendenze.
Condizione di blocco: l'aggiunta di una casella IMAP richiede una dipendenza non
presente o non puo` essere salvata senza esporre credenziali.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R03-T01-AC1` Caselle spiega che Google richiede il collegamento dedicato e rende immediata l'alternativa IMAP. | Test vista con Google non configurato e ispezione dei testi visibili. | `test_account_view_explains_imap_alternative_when_google_is_not_ready`: azione `Scegli Posta IMAP` e indicazione distinta da Google. | `MET` |
| `R03-T01-AC2` L'utente puo` selezionare IMAP, compilare nome, indirizzo, password e parametri avanzati quando necessari. | Test controller/UI con campi fake. | `test_selecting_imap_removes_google_dependency_and_saves_first_mailbox`: la scelta IMAP rimuove l'host Google, mostra i parametri richiesti e accetta password, server e porta. | `MET` |
| `R03-T01-AC3` Aggiungi casella salva una prima casella IMAP tramite il servizio condiviso e mostra la riga nell'elenco. | Test `AccountManagementService` con credential store fake. | Lo stesso test salva tramite `AccountManagementService`, legge la casella persistita e verifica l'host IMAP; prova nuova `1 passed`. | `MET` |
| `R03-T01-AC4` Completa configurazione senza caselle indica la singola azione necessaria; con una casella salvata apre Home. | Test controller successo/blocco. | `test_first_run_finishes_explicitly_on_home_without_restart` e nuovo test IMAP coprono blocco senza casella, azione coerente e apertura Home dopo il salvataggio. | `MET` |
| `R03-T01-AC5` Dopo riapertura la casella salvata e` modificabile senza mostrare segreti o termini tecnici. | Test persistenza fake e inventario stringhe GUI. | Evidenze gia` acquisite in `test_home_reopens_existing_configuration_and_returns_after_edit`, `test_two_accounts_persist_after_shell_is_closed_and_reopened` e inventario delle stringhe vietate; non ripetute in questa run. | `MET` |

#### GUI-U-R03-T02 - Seconda casella e verifica collegamento

Stato: `DONE`.
Risultato: da una configurazione con la prima casella salvata, l'utente aggiunge
una seconda casella con credenziali indipendenti e verifica il collegamento
senza bloccare la finestra, mantenendo entrambe le caselle dopo il riavvio.
Dipendenza: `GUI-U-R03-T01 = DONE`; servizi esistenti di gestione caselle,
credenziali e verifica read-only.
Componenti ammessi: vista Caselle, controller, `AccountManagementService`,
`BackgroundAccountConnectionCheck`, feedback Home, test con fake e
documentazione minima.
Esclusioni: rete o credenziali reali nei test, nuovo OAuth, GUI legacy, Registro,
Apps Script, pipeline e nuove dipendenze.
Condizione di blocco: la seconda casella non puo` mantenere credenziali distinte
oppure la verifica richiede rete reale o blocca il thread della GUI.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R03-T02-AC1` Da Impostazioni e` possibile aggiungere una seconda casella senza alterare la prima. | Test controller con configurazione contenente una casella. | `test_account_crud_supports_different_providers_and_separate_credentials` aggiunge due caselle tramite il servizio condiviso e conserva la prima. | `MET` |
| `R03-T02-AC2` Le due caselle conservano credenziali distinte e non mostrano segreti nell'elenco o nei messaggi. | Test credential store fake e inventario visibile. | `test_account_crud_supports_different_providers_and_separate_credentials` usa il credential store fake per valori distinti; `test_multi_account_view_has_no_forbidden_technical_terms` esclude termini tecnici dalla vista. | `MET` |
| `R03-T02-AC3` Verifica collegamento usa il percorso del provider selezionato, non blocca la finestra e mostra un esito azionabile. | Test asincrono deterministico con adapter fake. | `test_connection_check_shows_immediate_progress_then_success_without_blocking` verifica adapter fake, riscontro immediato e completamento asincrono. | `MET` |
| `R03-T02-AC4` Modifica, attivazione e rimozione della seconda casella non danneggiano la prima. | Test CRUD mirato tramite servizio condiviso. | `test_account_crud_supports_different_providers_and_separate_credentials` verifica aggiornamento, attivazione e rimozione senza alterare l'altra casella. | `MET` |
| `R03-T02-AC5` Dopo riapertura entrambe le caselle e il loro stato sono visibili nella GUI. | Test persistenza e reingresso con filesystem e credenziali fake. | `test_two_accounts_persist_after_shell_is_closed_and_reopened` ritrova entrambe le caselle persistite e apre Home dopo il riavvio. | `MET` |

Successivo univoco dopo la chiusura: `GUI-U-R03-T03`.

#### GUI-U-R03-T03 - Percorso reale completo, Riepilogo e Home

Stato: `DONE`.
Risultato: il primo avvio reale percorre Benvenuto, Limbo, Caselle, Riepilogo e
Home in una sola finestra, conserva i dati e soddisfa i requisiti UX R2 non
ancora dimostrati sul prodotto operativo.
Dipendenza: `GUI-U-R03-T02 = DONE`.
Componenti ammessi: viste e controller `user_app`, servizi condivisi di
configurazione e caselle, Home, test fake/Tk mirati e documentazione minima.
Esclusioni: percorso demo come prodotto, GUI legacy, nuovi toolkit, rete o dati
reali nei test, Apps Script, Registro, pipeline e nuove dipendenze.
Condizione di blocco: il Riepilogo reale richiede duplicazione della logica
applicativa o il percorso non puo` restare utilizzabile a 960x640.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R03-T03-AC1` Il percorso reale attraversa le cinque viste in una finestra e conserva i dati usando Indietro/Continua. | Test di routing/controller con servizi fake persistenti. | `test_real_first_run_keeps_data_through_summary_back_and_home` percorre Benvenuto, Limbo, Caselle, Riepilogo, ritorno a Caselle e Home, poi riapre le due caselle persistite. | `MET` |
| `R03-T03-AC2` Riepilogo mostra Limbo, caselle, stati, incompletezze e correzioni; `Completa configurazione` apre Home. | Test vista/controller sul modello reale. | Lo stesso test verifica Limbo, due caselle, conteggio/stato attivo, casella da attivare, azione di correzione e `Completa configurazione`; il secondo Continua apre Home. | `MET` |
| `R03-T03-AC3` Home mostra stato, caselle, prossima azione, attivita`, problemi e Impostazioni dai servizi condivisi. | Test Home con servizi fake e stati deterministici. | `test_home_renders_main_general_states`, `test_home_has_exactly_the_three_primary_actions`, `test_demo_home_makes_status_next_action_activity_and_problems_visible` e `test_home_reopens_existing_configuration_and_returns_after_edit`, rieseguiti nel gruppo mirato, coprono dati e azioni della Home condivisa. | `MET` |
| `R03-T03-AC4` Le cinque viste restano utilizzabili a 960x640 e scala 100%/125%. | Solo prova Tk/resize interessata dalle nuove viste; riuso delle evidenze invariate. | `test_first_run_demo_fits_real_tk_window_at_960x640_for_supported_scales` ora usa Tk reale anche sul percorso persistente e verifica Riepilogo/Home a 100% e 125%; la prima prova ha rilevato 971 px e ha guidato il wrapping poi verde. | `MET` |
| `R03-T03-AC5` Testi ed errori non espongono termini tecnici e indicano sempre problema e azione. | Inventario delle sole stringhe nuove o modificate. | `test_complete_visible_text_inventory_has_no_technical_or_legacy_terms`, rieseguito con il Riepilogo reale, esclude i termini vietati nelle stringhe visibili; i riscontri restano azionabili. Gruppo mirato finale: `39 passed`. | `MET` |

#### GUI-U-R03-R06 - Consegna operativa a Da archiviare

Stato: `DONE` (approvato e completato il 2026-07-24).
Risultato: `Controlla ora` e il controllo continuo portano ogni allegato sicuro
dal Limbo sincronizzato a una singola presa in carico in `Da archiviare`; il
messaggio sorgente viene completato soltanto dopo tale presa in carico.
Dipendenze: `GUI-U-R03-R04 = DONE`; servizi esistenti
`DriveStagingVerifyClient` e `DaArchiviareIntakeHttpClient`; endpoint Apps
Script gia` contrattualizzati e cartella Limbo sincronizzata.
Componenti ammessi: risposta della verifica Drive, orchestrazione della
pipeline locale, stato/eventi locali, completamento dei messaggi, traduzione
business delle attivita`, test con adapter fake e documentazione minima.
Esclusioni: rete o credenziali reali nei test, invio di byte/base64/path locali
ad Apps Script, modifica del form, sostituzione di Apps Script, nuove
dipendenze, GUI legacy, redesign delle viste e disinstallatore diretto.
Condizione di blocco: gli endpoint esistenti non restituiscono ID Drive stabili
oppure non consentono di distinguere in modo sicuro attesa di sincronizzazione,
errore e presa in carico idempotente senza ampliare il contratto approvato.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R03-R06-AC1` La verifica cloud conserva e valida gli ID del file e del manifest restituiti nell'anteprima esistente, senza trasferire contenuti o percorsi locali. | Test contratto su risposta valida, ID mancanti/incoerenti e payload metadata-only. | `DriveStagingVerifyResponse` estrae i due ID dall'`inbox_preview` gia` restituito, li richiede quando `cloud_visible=true` e rifiuta tipi o valori assimilabili a percorsi; il test del payload conferma soli metadati. Il codice di collegamento resta nel Gestore credenziali Windows e non entra nel file di configurazione. | `MET` |
| `R03-R06-AC2` Per ogni allegato sicuro copiato nel Limbo la pipeline verifica la visibilita` cloud e crea automaticamente una sola voce in `Da archiviare`. | Test verticale con scanner, storage, verify e intake fake su uno o piu` allegati. | La nuova fase condivisa `OperationalHandoffRunner` compone i client CLI esistenti tra storage e completion; prove con uno e due allegati verificano verify e intake per ciascun manifest. Il worker installato recupera automaticamente da Windows credenziali caselle e collegamento, mantenendo priorita` alle variabili dei comandi CLI. | `MET` |
| `R03-R06-AC3` Sincronizzazione non ancora avvenuta, timeout o rifiuto lasciano il lavoro in attesa/riprova e non completano ne` spostano il messaggio sorgente. | Regressioni deterministiche sugli esiti temporanei e permanenti, con verifica dell'ordine delle chiamate. | Verify non visibile produce `waiting` senza intake; eccezione o rifiuto intake producono evento riprovabile; `LocalCompletionRunner(require_da_archiviare=True)` non apre la casella finche` manca un intake riuscito. | `MET` |
| `R03-R06-AC4` Una nuova esecuzione e una risposta di presa in carico gia` esistente non producono duplicati e permettono il completamento sicuro. | Test di ripetizione sulla stessa identita` tecnica e risposta idempotente dell'intake fake. | Un evento locale `created`, `updated` o `idempotent` rende il retry `already_delivered` senza nuove chiamate; un errore resta riprovabile e il completamento procede dopo l'esito idempotente. | `MET` |
| `R03-R06-AC5` Home e Attivita` descrivono in termini utente consegna riuscita, attesa di sincronizzazione o problema azionabile; test mirati e smoke locale sono verdi. | Test dei modelli/testi visibili, inventario termini vietati e smoke locale. | Attivita traduce consegna, sincronizzazione e problema con azioni comprensibili; `Registro e avvio` configura indirizzo e codice senza termini tecnici e resta entro 960x640 a 100%/125%. Mirati collegamento/handoff/UI `92 passed`, Tk reale `1 passed`; smoke finale `529 passed` (una prima esecuzione: `528 passed` e un errore transitorio Tcl/Tk preesistente, non riprodotto a toolchain libera). | `MET` |

### GUI-U-R04 - Release candidate e collaudo finale

Stato: `IMPLEMENTED_NOT_ACCEPTED`.
Risultato: una release candidate identificata viene installata, usata e rimossa
con successo su un PC o profilo Windows senza Python utilizzabile dall'utente,
eseguendo l'intero percorso finale senza terminale o documentazione tecnica.
Dipendenza: `GUI-U-R03 = DONE` dopo conferma umana esplicita e
`GUI-U-R03-R06 = DONE`.
Componenti ammessi: sorgente accettata in R03, pipeline build/installer R01,
smoke di release, applicazione installata, integrazioni Windows gia` approvate,
manifest/hash, checklist ed evidenze del collaudo finale.
Esclusioni: nuove funzioni, redesign, correttivi non approvati, servizi o dati
reali nei test automatici, uso di terminale/Python o modifica manuale di file
durante il collaudo umano, merge, `clasp push` e modifica di `main`.
Condizione di blocco: non e` disponibile un ambiente Windows idoneo senza Python,
la release candidate non coincide con commit/hash/build ID attesi, oppure un
prerequisito R03 non ha ricevuto conferma umana esplicita.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R04-AC1` Hash e build-info coincidono con il manifest; installazione e avvio dal menu Start riescono su ambiente idoneo. | Smoke release e passi umani 1-4 con installer, hash, commit e build ID registrati. | RC `CaronteSetup-0.11.0-bab6e92.exe`, commit `bab6e920994953cf908b9fc4f09d6d06fc1d5f15`, Build ID `e7bd442d-8a34-4181-ba52-5f2d07ebb987`, SHA-256 `B5B23124ABCEA65ED61A78808961992228C501426A4C08559048A0E9DB4AC238`; build/smoke `PASS` e conferma umana di installazione e avvio acquisita il 2026-07-25. | `MET` |
| `R04-AC2` Primo avvio, Limbo, due caselle, riapertura, persistenza, controllo manuale, avvio continuo, pausa e attivita` completano il percorso senza strumenti tecnici. | Collaudo umano dei passi 5-13 con evidenze puntuali. | Pipeline, Registro, controllo manuale/continuo, pausa, Home e Attivita funzionano sulla RC `bab6e92`, ma il documento entra nella coda tecnica senza notifica o collegamento al form Virgilio. Il percorso umano resta incompleto; controllo lento senza fase/conteggio e lessico cartelle fuorviante sono consolidati. | `NOT_MET` |
| `R04-AC3` Controllo automatico, riavvio sessione o simulazione equivalente, verifica stato, disattivazione, Impostazioni e Informazioni funzionano in sequenza. | Collaudo umano dei passi 14-19 e confronto finale dell'identita build. | `H-R03-06 = PASS` resta valido; persistenza OAuth, Manutenzione sempre accessibile, Impostazioni, Informazioni e identita` della RC `bab6e92` confermate dall'utente il 2026-07-25. | `MET` |
| `R04-AC4` Disinstallazione rimuove programma e integrazioni e applica la policy dichiarata di conservazione dati. | Smoke disinstallazione e collaudo umano dei passi 20-22. | Smoke installer/disinstallazione `PASS`; disinstallazione standard Windows, rimozione integrazioni e conservazione prevista confermate dall'utente il 2026-07-25. L'avvio diretto del disinstallatore resta escluso. | `MET` |
| `R04-AC5` Tutti gli scenari obbligatori sono `PASS`, nessuno e` `FAIL` o `INVALID_BUILD`, e il fascicolo contiene identificazione ed evidenze complete. | Revisione umana della checklist e verifica documentale del fascicolo finale. | Il fascicolo della RC `bab6e92` identifica correttamente la build, ma il `FAIL` funzionale interrompe il gate. Un nuovo fascicolo verra` prodotto da `R04-R06`. | `NOT_MET` |

Esito umano della RC `bab6e92` del 2026-07-25: `FAIL` funzionale sul percorso
verso la decisione umana. R04 e l'iniziativa GUI-U possono essere dichiarati
completati solo dopo i correttivi `R04-R03`--`R04-R06`, la pubblicazione umana
Apps Script e un nuovo `PASS` umano esplicito.

#### GUI-U-R04-R01 - Configurazione amministrativa comprensibile

Stato: `DONE`.
Risultato: la schermata quotidiana di Caronte non chiede indirizzi o codici
tecnici; Caronte Manutenzione, raggiungibile dalla GUI e dal menu Start,
spiega e salva in un solo punto Registro condiviso e servizio di consegna.
Dipendenze: `GUI-U-R03-R06 = DONE`; `GUI-U-R04 = WAITING_HUMAN_REVIEW`;
feedback umano del 2026-07-24 con schermata allegata.
Componenti ammessi: vista `Registro e avvio`, nuova `maintenance_gui`, servizi
applicativi condivisi, launcher, installer, test e documentazione R04.
Esclusioni: modifica di Apps Script, nuovi protocolli o segreti versionati,
campi tecnici nella GUI utente, privilegi amministrativi, legacy `gui`/`gui_*`,
disinstallatore diretto, `clasp push`, merge e modifica di `main`.
Condizione di blocco: i dati operativi non possono essere salvati tramite i
servizi esistenti oppure la manutenzione non puo` essere aperta dalla build
installata senza terminale.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R04-R01-AC1` La GUI utente non mostra ne` richiede URL, codici o istruzioni amministrative indecifrabili. | Test inventario widget/testi e confronto con la schermata del FAIL. | Rimossi indirizzo, codice e salvataggio dalla vista utente; la pagina mostra soltanto Registro/Consegna pronti o non pronti e una singola azione `Apri Caronte Manutenzione`. Il test vieta anche la vecchia istruzione `chiedi all'amministratore`. | `MET` |
| `R04-R01-AC2` Caronte Manutenzione spiega origine e significato di Registro, indirizzo del servizio e chiave di accesso e li salva tramite servizi condivisi. | Test GUI con servizi fake e persistenza protetta. | La manutenzione identifica il foglio Google, indica `Gestisci deployment` e l'indirizzo `/exec`, identifica `VIRGILIO_TOKEN` nelle proprieta` dello script e dichiara la protezione Windows. Salvataggio con servizi condivisi verificato; una chiave gia` protetta puo` essere mantenuta lasciando vuoto il campo. | `MET` |
| `R04-R01-AC3` Dalla schermata utente si apre Caronte Manutenzione senza console e senza privilegi amministrativi. | Test launcher iniettato e comando frozen. | Azione utente e fallimento guidato verificati; il comando frozen richiama lo stesso `Caronte.exe maintenance-gui --config ...`, con `CREATE_NO_WINDOW`, senza Python o elevazione. | `MET` |
| `R04-R01-AC4` L'installer crea nel menu Start accessi distinti a Caronte e Caronte Manutenzione e li rimuove insieme. | Test installer e smoke installato. | Installer crea `Caronte.lnk` e `Caronte Manutenzione.lnk` con argomenti distinti nella stessa cartella rimossa dalla disinstallazione; lo smoke installato apre entrambe le finestre. | `MET` |
| `R04-R01-AC5` Test mirati, Tk reale e smoke locale sono verdi e viene prodotta una nuova RC identificata. | Suite mirata, smoke e manifest/hash della RC. | Mirati finali `35 passed`; Tk isolato `1 passed`; smoke locale `532 passed`. La nuova RC con client OAuth locale viene prodotta dal commit conclusivo e identificata dal relativo manifest ignorato. | `MET` |

#### GUI-U-R04-R02 - Registro Google realmente operativo

Stato: `DONE`.
Risultato: `Collega Google` usa il client OAuth incluso, apre il consenso nel
browser e conserva l'autorizzazione Sheets nel Gestore credenziali Windows; i
controlli Home aggiornano il Registro tramite il servizio CLI gia` esistente e
Caronte Manutenzione resta sempre raggiungibile.
Dipendenze: `GUI-U-R04-R01 = DONE`; feedback umano del 2026-07-25 sulla RC
`24d54be`.
Componenti ammessi: OAuth Google condiviso, credenziali Windows, gateway
Bucoliche, pipeline locale, vista `Registro e avvio`, test, build e documenti
R04.
Esclusioni: credenziali o rete reali nei test, token su file, modifica Apps
Script, nuovi protocolli, legacy `gui`/`gui_*`, disinstallatore diretto,
`clasp push`, merge e modifica di `main`.
Condizione di blocco: il client OAuth incluso non supporta lo scope Google
Sheets oppure l'export Bucoliche esistente non puo` essere composto prima del
completamento del messaggio.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R04-R02-AC1` `Collega Google` usa il client Desktop incluso e apre il browser con lo scope Google Sheets, senza file o variabili esterne. | Test del flusso con client e flow fake. | `GoogleSheetsOAuthService` carica la stessa risorsa Desktop inclusa nella build e avvia il loopback su `127.0.0.1` con browser e solo scope Sheets. La vista spiega prima del click che si aprira` il browser e richiede un account capace di modificare il foglio. | `MET` |
| `R04-R02-AC2` L'autorizzazione Sheets viene salvata, riletta e rinnovata soltanto nel Gestore credenziali Windows. | Test con credential store fake, refresh e scansione persistenza. | Autorizzazione opaca salvata in `VIRGILIO_BUCOLICHE_GOOGLE_OAUTH` tramite il `CredentialStore`; lettura, refresh e sostituzione protetta verificati senza token su configurazione o file. | `MET` |
| `R04-R02-AC3` Il controllo manuale/continuo esporta gli eventi nel Registro prima di completare il messaggio e un errore Registro lascia il lavoro riprovabile. | Test pipeline verticale con exporter fake su successo ed errore. | `LocalPipelineRunner` compone l'adapter CLI `BucolicheAppendOnlyAdapter` dopo la consegna e prima del completamento. Successo verifica ordine `handoff -> registry -> completion`; errori/assenza credenziale bloccano completion. Un Registro gia` selezionato ma disabilitato viene migrato automaticamente; sezioni e intestazioni mancanti vengono predisposte dopo l'autorizzazione. | `MET` |
| `R04-R02-AC4` `Apri Caronte Manutenzione` resta disponibile anche dopo una configurazione completa. | Test inventario e callback della vista configurata. | Pulsante e testo per interventi futuri sono sempre presenti; callback verificata sia su configurazione incompleta sia completa. | `MET` |
| `R04-R02-AC5` Test mirati, Tk reale, smoke locale e nuova RC identificata sono verdi. | Suite focalizzata, smoke e manifest/hash RC. | Mirati finali `72 passed`; smoke locale finale `540 passed`. Una prima esecuzione aveva completato `539 passed` prima dell'errore intermittente di caricamento `init.tcl`, non riprodotto al secondo smoke. La nuova RC viene prodotta dal commit conclusivo con client OAuth incluso. | `MET` |

#### GUI-U-R04-R03 - Notifica operativa e accesso a Virgilio

Stato: `DONE`.
Risultato: ogni nuovo documento preso in carico genera un collegamento univoco
al form Virgilio e una notifica osservabile sui canali configurati, senza
duplicare righe o messaggi durante i retry.
Dipendenze: `GUI-U-R04-R02 = DONE`; `FAIL` umano RC `bab6e92`.
Componenti ammessi: `apps_script/src/virgilio_inbox.gs`,
`apps_script/src/notifiche.gs`, contratto intake locale, test puri Apps Script
e Python, documentazione del task.
Esclusioni: modifica invasiva del form, nuovi canali, servizi o credenziali
reali nei test, `clasp push`, deploy, segreti versionati e GUI legacy.
Condizione di blocco: l'URL `/exec` del form non puo` produrre un link con
`inbox_id`, oppure i canali esistenti non possono restituire un esito
osservabile senza cambiare protocollo.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R04-R03-AC1` Una nuova riga riceve e restituisce un `form_url` assoluto costruito dall'URL del deployment e dal proprio `inbox_id`. | Test puro Apps Script su URL valido, parametri esistenti, caratteri speciali e configurazione assente. | Harness Node/VM locale: `/exec?x=1` + `inbox_id` codificato, configurazione assente rifiutata; nessuna rete. | `MET` |
| `R04-R03-AC2` La creazione invia ai canali configurati un messaggio leggibile con documento, provenienza e azione `Apri in Virgilio`, senza dati tecnici o segreti. | Test con adapter Chat/Telegram fake e inventario del testo. | Harness puro con adapter Chat/Telegram fake: due invii, testo con documento/provenienza/`Apri in Virgilio`, senza `inbox_id`. | `MET` |
| `R04-R03-AC3` Retry idempotenti non duplicano riga o notifica; un invio non riuscito resta osservabile e riprovabile. | Test deterministico su creazione, retry riuscito e fallimento/ripresa della notifica. | Fake Sheet/adapter: seconda presa in carico riusa la riga e `notification_status=sent` evita il secondo invio; esiti `retry` restano nel metadata per il ciclo successivo. | `MET` |
| `R04-R03-AC4` Il client locale conserva link ed esito notifica nel contratto metadata-only e non completa il passaggio se il lavoro non e` raggiungibile. | Test verticale Python con risposte fake valide, incomplete e idempotenti. | `25 passed`: contratto conserva URL/stato, accetta URL codificato e rifiuta link/stato assenti; handoff registra URL/stato e tratta l'errore come riprovabile. | `MET` |
| `R04-R03-AC5` Prove mirate Apps Script/Python, diff e scansione segreti sono verdi senza rete reale. | Harness locale e test mirati; nessun `clasp push`. | Harness Apps Script puro `OK`; pytest mirato `25 passed`; smoke locale `545 passed`; diff/check e scansione segreti finali verdi; nessun push/deploy. | `MET` |

#### GUI-U-R04-R04 - Avanzamento del controllo osservabile

Stato: `DONE`.
Risultato: durante un controllo lento la Home mostra sempre che Caronte sta
procedendo, la fase corrente e un conteggio utile, restando reattiva.
Dipendenza: `GUI-U-R04-R03 = DONE`.
Componenti ammessi: runner e feedback applicativi condivisi, Home, Attivita e
test fake/Tk.
Esclusioni: nuove finestre, log tecnici, stime temporali inventate, GUI legacy.
Condizione di blocco: il runner non puo` emettere avanzamenti intermedi senza
duplicare la pipeline o bloccare la finestra.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R04-R04-AC1` `Controlla ora` mostra immediatamente attivita e fase corrente fino all'esito finale. | Test asincrono con runner lento e fasi deterministiche. | Runner in background emette eventi strutturati di fase; Home li traduce durante il controllo. `test_user_app_operational_feedback.py` e `test_user_app_home_control.py` verdi. | `MET` |
| `R04-R04-AC2` La Home mostra documenti trovati, elaborati e rimanenti quando noti, senza fingere percentuali. | Test su zero, uno e piu documenti. | La pipeline pubblica soltanto i conteggi realmente disponibili; test fake verifica zero e Home mostra i tre campi senza percentuali. | `MET` |
| `R04-R04-AC3` Controllo continuo e pausa aggiornano lo stesso segnale senza processi duplicati. | Test avvio, ciclo, pausa durante una fase e riapertura. | Il runner posseduto resta unico; test di avvio continuo, doppio avvio, pausa e chiusura verde. | `MET` |
| `R04-R04-AC4` Errori e attese sostituiscono il progresso con un messaggio e un'azione comprensibili. | Test su sincronizzazione, rete e Registro fake. | Attesa Registro ed errore di collegamento hanno messaggi azionabili e senza dettagli runtime; fake test verde. | `MET` |
| `R04-R04-AC5` GUI reattiva, testi consentiti e layout 960x640 a 100%/125% sono verificati. | Test Tk interessato e inventario stringhe. | Tk reale a 960x640/100%/125% `1 passed`; inventario delle stringhe utente e smoke `549 passed` verdi. | `MET` |

#### GUI-U-R04-R05 - Cartelle della casella coerenti

Stato: `DONE`.
Risultato: la GUI mostra soltanto le cartelle email realmente usate dal
percorso ordinario e non promette uno spostamento che la configurazione non
esegue.
Dipendenza: `GUI-U-R04-R04 = DONE`.
Componenti ammessi: modello/presentazione caselle, migrazione non distruttiva
della configurazione, testi Home/Attivita e test.
Esclusioni: attivare automaticamente scritture IMAP, cancellare o spostare
messaggi, cambiare il Limbo, GUI legacy.
Condizione di blocco: nascondere il campo non consente di preservare senza
perdita configurazioni esistenti.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R04-R05-AC1` Il percorso ordinario espone la cartella da controllare ma non `Cartella completati` finche il completamento IMAP resta disabilitato. | Test inventario vista primo avvio/Impostazioni. | `test_operational_folders_hide_non_operational_completion_and_preserve_it` e il test di inventario della vista verificano che il campo non sia presente e restino le sole cartelle operative. | `MET` |
| `R04-R05-AC2` Modifica e riapertura preservano internamente i valori esistenti senza abilitarli. | Test round-trip su configurazione precedente. | La modifica della cartella da controllare e la riapertura mantengono `done_folder` interno; le nuove caselle ricevono il solo default interno. | `MET` |
| `R04-R05-AC3` Home e Attivita distinguono documento acquisito, lavoro disponibile in Virgilio e pratica archiviata. | Test proiezione eventi e testi visibili. | Nuovo test proietta esplicitamente `Documento acquisito`, `Lavoro disponibile in Virgilio` e `Pratica archiviata`. | `MET` |
| `R04-R05-AC4` Nessun messaggio sorgente viene copiato, mosso o cancellato implicitamente. | Regressione adapter IMAP read-only. | `test_completion_ack_disabled_skips_without_imap` verde: completamento disabilitato non apre IMAP. | `MET` |
| `R04-R05-AC5` Test mirati e inventario terminologico sono verdi. | Suite focalizzata senza servizi reali. | Mirati fake `44 passed`; smoke locale `550 passed`, senza servizi o credenziali reali. | `MET` |

#### GUI-U-R04-R06 - Release candidate del pilota corretto

Stato: `DONE`.
Risultato: una nuova RC identificata e un fascicolo minimo permettono di
pubblicare il solo delta Apps Script autorizzato e collaudare notifica, accesso
al form, progresso e lessico corretto.
Dipendenze: `GUI-U-R04-R03`--`R04-R05 = DONE`.
Componenti ammessi: build/installer, smoke release, manifest/hash, checklist,
diff Apps Script pronto per revisione e documentazione operativa.
Esclusioni: `clasp push` automatico, deploy automatico, credenziali reali nei
test, merge, `main`, disinstallatore diretto.
Condizione di blocco: diff Apps Script non riconciliato col progetto collegato,
smoke non verde o identita della build non univoca.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| `R04-R06-AC1` Tutti i criteri dei tre correttivi hanno evidenza specifica e i relativi test sono verdi. | Revisione tabelle e prove registrate. | R04-R03: harness Apps Script puro `OK`, fake `25 passed`, smoke `545 passed`; R04-R04: `113 passed`, Tk `1 passed`, smoke `549 passed`; R04-R05: `44 passed`, smoke `550 passed`. | `MET` |
| `R04-R06-AC2` Il delta Apps Script e` limitato, senza segreti e pronto per approvazione/push umano. | `clasp status`, diff e scansione segreti; nessun push. | `clasp 3.3.0 status` elenca solo i 12 file attesi in `apps_script/src`, senza untracked; diff limitato ai correttivi R04-R03 e nessun push/pull/deploy eseguito. | `MET` |
| `R04-R06-AC3` Build e installer autonomi superano gli smoke richiesti. | Build pulita, smoke build e installer. | Pipeline locale da albero pulito, toolchain Windows `3.13.14`/PyInstaller `6.21.0`: build e installer `PASS`, smoke build e installer `PASS`. | `MET` |
| `R04-R06-AC4` Manifest registra installer, SHA-256, commit, build ID e client OAuth incluso. | Confronto automatico artefatti/manifest. | Il manifest release locale registra installer, SHA-256, commit e build ID; confronto hash verde e `oauth_client_included=true` corrisponde alla risorsa inclusa. Test manifest `13 passed`. | `MET` |
| `R04-R06-AC5` Checklist pilota riprova solo notifica/link, avanzamento e lessico; i PASS invariati non vengono ripetuti. | Revisione documentale del fascicolo. | Checklist R04 ridotta a notifica/link, fasi/conteggi e lessico cartelle; gli scenari gia` `PASS` non sono inclusi. | `MET` |

Dopo `R04-R06` l'automazione deve fermarsi al gate umano di pubblicazione Apps
Script. Solo un task esplicito autorizzato puo` eseguire `clasp push`; il
successivo collaudo reale della RC resta una decisione umana.

## GUI-U-R05 - Chiusura strutturale del percorso operativo

Stato: `WAITING_HUMAN_REVIEW`.
Origine: collaudo umano del 2026-07-26. Il percorso CLI/GAS e i suoi contratti
restano canonici; i correttivi riguardano regressioni e composizione nella build
Desktop, non una nuova implementazione del flusso.
Obiettivo: ottenere una sola build in cui acquisizione, quarantena, Limbo, `Da
archiviare` e Registro avanzano coerentemente anche dopo ripristino o nuova
installazione.
Esclusioni comuni: redesign UX, refactor preventivi, nuovi server o database,
riscrittura del form, sostituzione del GAS, servizi reali nei test.

### GUI-U-R05-T01 - Recupero artefatti locali e fallimento storage osservabile

Stato: `DONE`. Priorita`: `P0`.
Risultato: un riferimento SQLite privo del file locale viene riparato dal
processor IMAP esistente e un errore storage blocca realmente la pipeline.
Dipendenze: nessuna.
Componenti ammessi: `multi_account`, `readonly_state`, `storage_adapter`,
`pipeline`, proiezione Attivita/Home e test interessati.
Condizione di blocco: la correzione richiede mutazioni IMAP o un nuovo protocollo.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| --- | --- | --- | --- |
| `R05-T01-AC1` Il duplicato e` valido solo con file e SHA-256 coerenti. | Fixture con record presente e file assente/corrotto. | Prova parametrica su file assente e corrotto: entrambi sono riscritti con SHA-256 atteso; il duplicato valido resta idempotente. | `MET` |
| `R05-T01-AC2` Il file mancante viene riacquisito tramite il downloader esistente. | Fake IMAP read-only e verifica file/manifest. | `MultiAccountImapProcessor` riusa `detect_attachments`, scanner e manifest esistenti e ripara la riga senza crearne una seconda. | `MET` |
| `R05-T01-AC3` `staging_failed` e `staging_conflict` sono persistiti e leggibili. | Test storage, audit e proiezione attivita`. | Entrambi gli stati sono salvati in SQLite, producono audit con motivo e sono proiettati come `Problema` azionabile. | `MET` |
| `R05-T01-AC4` Un errore storage rende la pipeline fallita e impedisce completion/handoff. | Test pipeline con factory fake. | Factory fake `staging_failed`: esito `completed_with_errors`, handoff e completion non invocati, errore descritto nel report. | `MET` |
| `R05-T01-AC5` Il percorso riparato arriva alla consegna. | Test verticale file mancante -> copia -> handoff; smoke. | Verticale fake read-only riacquisisce due file mancanti, li copia nel Limbo e li consegna; mirati `79 passed`, smoke `558 passed`. | `MET` |

### GUI-U-R05-T02 - Ripristino locale coordinato

Stato: `DONE`. Priorita`: `P0`.
Risultato: il reset locale esistente viene composto con stop runner, lock,
backup verificato e successiva nuova acquisizione.
Dipendenze: `R05-T01 = DONE`.
Componenti ammessi: servizi runner/startup, `reset_local_state`,
`MaintenanceService`, CLI condivisa e test fake.
Condizione di blocco: impossibile garantire esclusione reciproca tra worker e reset.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| --- | --- | --- | --- |
| `R05-T02-AC1` Nessun reset parte con un runner attivo. | Test lock e worker concorrente. | Lock interprocesso condiviso da pipeline/reset; worker posseduto fermato prima del reset e reset concorrente rifiutato senza modifiche. | `MET` |
| `R05-T02-AC2` Il backup precede ogni modifica ed e` verificato. | Fixture filesystem e controllo inventario. | Inventari relativi, dimensioni e SHA-256 di sorgente/copia coincidono prima della rimozione; mismatch lascia la radice invariata. | `MET` |
| `R05-T02-AC3` Configurazione e credenziali restano; DB/quarantena sono ricreati. | Round-trip servizi con credenziali fake. | Config esterna e `FakeCredentialStore` invariati; `state.db` canonico e quarantena vuota ricreati. | `MET` |
| `R05-T02-AC4` L'esito espone conservato, azzerato e percorso backup. | Test servizio e presentazione tecnica. | Risultati servizio/CLI espongono `preserved`, `reset` e `backup_path`; summary tecnico mostra conservato e azzerato. | `MET` |
| `R05-T02-AC5` Il primo ciclo successivo riacquisisce e copia. | Test verticale con fake IMAP/storage. | Dopo reset, processor fake IMAP riacquisisce PDF e storage fake lo copia fuori dalla radice locale. | `MET` |

Prove automatiche: test mirati `75 passed`; smoke locale `563 passed`.

### GUI-U-R05-T03 - Azzeramento coerente ambiente TEST

Stato: `DONE`. Priorita`: `P0`.
Risultato: una sola operazione amministrativa, costruita sugli helper CLI/GAS
esistenti, riallinea stato locale, Registro TEST, `Da archiviare` TEST e Limbo
TEST con backup e ripresa idempotente.
Dipendenze: `R05-T02 = DONE`.
Componenti ammessi: servizi manutenzione, client HTTP metadata-only, setup e
harness GAS esistenti, foglio e cartelle esclusivamente TEST.
Condizione di blocco: ambiente non marcato TEST, identificativi non univoci o
mancanza di autorizzazione umana per pubblicazione/esecuzione reale.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| --- | --- | --- | --- |
| `R05-T03-AC1` Anteprima elenca esattamente righe, file e stato locale coinvolti. | Harness fake locale/GAS. | Client metadata-only e servizio espongono file e conteggi tabelle locali; GAS espone righe, file e schema dei tre asset TEST. Test mirato e harness puri verdi. | `MET` |
| `R05-T03-AC2` Backup locale, copia Registro e cartella Drive datata precedono l'azzeramento. | Test ordine chiamate e fallimenti. | `prepare` crea/reusa prima le copie Registro/Limbo; solo dopo il reset locale canonico parte `execute`. Harness verifica l'ordine completo. | `MET` |
| `R05-T03-AC3` Solo asset marcati TEST possono essere modificati. | Test rifiuto ID/ambiente non TEST. | GAS richiede ambiente `TEST`, nome TEST per ogni asset e tre ID univoci; harness rifiuta PROD e ID duplicati. | `MET` |
| `R05-T03-AC4` Lo stesso `reset_id` riprende senza duplicazioni. | Test interruzione dopo ogni fase. | Stato GAS persistito dopo ogni fase, nomi backup deterministici e marker locale atomico rendono retry idempotente; harness riparte da tutte le sei fasi. | `MET` |
| `R05-T03-AC5` Dopo il reset i quattro stati sono vuoti e coerenti, con schema preservato. | Harness integrato senza servizi reali. | Il coordinatore accetta il completamento solo con righe Registro/Inbox e file Limbo vuoti e header invariati; DB/quarantena locali sono ricreati vuoti. `91 passed`, harness GAS `OK`, smoke `571 passed`. | `MET` |

### GUI-U-R05-T04 - Audit stabile e release finale

Stato: `DONE`. Priorita`: `P0`.
Risultato: il Registro riceve solo transizioni nuove; una RC identificata supera
il percorso completo e resta pronta per gli ultimi gate umani.
Dipendenze: `R05-T01`--`R05-T03 = DONE`.
Componenti ammessi: audit/export esistenti, test end-to-end, build/installer,
manifest e documentazione di collaudo minima.
Condizione di blocco: suite non verde, delta GAS non riconciliato o build non
identificabile.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| --- | --- | --- | --- |
| `R05-T04-AC1` Un controllo invariato non aggiunge eventi operativi duplicati. | Due cicli identici su fixture. | Lo store confronta l'ultimo stato dell'entita`: due retry completi sulla stessa fixture lasciano invariati i 10 eventi operativi. | `MET` |
| `R05-T04-AC2` Una transizione reale produce un solo evento ed export idempotente. | Test audit/Registro fake. | Stato invariato riusa lo stesso ID, uno stato diverso crea un solo nuovo evento; l'adapter fake esporta ogni transizione una volta e non riappende nei retry. | `MET` |
| `R05-T04-AC3` Il percorso email -> Limbo -> Da archiviare -> Registro e` verde. | Harness integrato senza rete reale. | Harness unico con IMAP/scanner, filesystem Limbo, verify/intake e Sheets fake attraversa le cinque transizioni per due allegati; mirati `45 passed`, smoke `572 passed`. | `MET` |
| `R05-T04-AC4` Build e installer identificati superano gli smoke. | Smoke build/installer e manifest hash. | Pipeline RC dal commit atomico del task: build e installer `PASS`; manifest esterno verifica nome, dimensione, SHA-256, commit, build ID e client OAuth incluso. | `MET` |
| `R05-T04-AC5` La checklist finale contiene solo pubblicazione, reset TEST autorizzato e collaudo reale. | Revisione fascicolo minimo. | La checklist R05 contiene esattamente i tre gate umani residui, senza ripetere prove automatiche o PASS storici. | `MET` |

Dopo `R05-T04` l'automazione si ferma. `clasp push`, deploy, azzeramento degli
asset Google reali e collaudo restano gate umani espliciti.
