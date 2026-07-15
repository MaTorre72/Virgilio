# EPIC GUI-U — Caronte Desktop utente

Stato: `IN_PROGRESS`
Sotto-epica attiva: `GUI-U-E1 - Fondazioni applicative`
Task corrente: `GUI-U-E1-T04 - Backend credenziali Windows`

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

Stato: `WAITING_FOR_PREVIOUS_TASKS`
Risultato: una casella viene configurata con campi ordinari e dettagli tecnici richiudibili.
Dipendenza: `GUI-U-E2-T02 = DONE`.
Componenti ammessi: vista account del wizard, servizi account/configurazione/credenziali, fake IMAP, test UI.
Esclusioni: seconda casella, controllo operativo, rete reale.
Condizione di blocco: il provider non puo` essere configurato senza mostrare un termine vietato nella vista ordinaria.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| I campi iniziali sono nome, email, password e stato attivo. | Test UI sull'inventario dei campi visibili. | — | `NOT_RUN` |
| Gmail/Workspace precompila host e porta. | Test UI sui default provider. | — | `NOT_RUN` |
| Le impostazioni avanzate sono richiudibili. | Test apertura/chiusura pannello. | — | `NOT_RUN` |
| Esiste un test read-only separato. | Test con fake IMAP che rifiuta mutazioni. | — | `NOT_RUN` |
| Nessun termine tecnico vietato e` visibile. | Test automatico sulle stringhe visibili. | — | `NOT_RUN` |

### GUI-U-E2-T04 — Multi-account

Stato: `WAITING_FOR_PREVIOUS_TASKS`
Risultato: l'utente gestisce almeno due caselle persistenti e indipendenti.
Dipendenza: `GUI-U-E2-T03 = DONE`.
Componenti ammessi: tabella caselle, CRUD account, servizi condivisi, fake credential store, test UI.
Esclusioni: controllo continuo, Home completa, rete reale.
Condizione di blocco: il modello o l'archivio credenziali non garantisce isolamento tra account.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste la tabella delle caselle. | Test UI su colonne e righe sintetiche. | — | `NOT_RUN` |
| Sono disponibili aggiunta, modifica e rimozione. | Test UI del ciclo CRUD. | — | `NOT_RUN` |
| Sono supportati server o provider differenti. | Test con due configurazioni diverse. | — | `NOT_RUN` |
| Le credenziali sono separate. | Test sui riferimenti e fake store. | — | `NOT_RUN` |
| I dati persistono dopo chiusura e riapertura. | Test round-trip della shell. | — | `NOT_RUN` |

### GUI-U-E2-T05 — Home minima

Stato: `WAITING_FOR_PREVIOUS_TASKS`
Risultato: la Home mostra stato essenziale e tre azioni comprensibili.
Dipendenza: `GUI-U-E2-T04 = DONE`.
Componenti ammessi: vista Home, view model stato, servizi runner fake, test UI.
Esclusioni: tabella attivita`, impostazioni complete, output tecnico.
Condizione di blocco: lo stato operativo non e` disponibile tramite un servizio indipendente dalla GUI tecnica.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| E` visibile lo stato generale. | Test UI sui principali stati sintetici. | — | `NOT_RUN` |
| E` visibile il numero di caselle attive. | Test view model con due account. | — | `NOT_RUN` |
| E` visibile l'ultimo controllo. | Test rendering timestamp Europe/Rome. | — | `NOT_RUN` |
| Esistono `Controlla ora`, `Avvia` e `Pausa`. | Test UI sulle tre azioni. | — | `NOT_RUN` |
| Non compare JSON o output CLI. | Test automatico sulle stringhe visibili. | — | `NOT_RUN` |

### GUI-U-E2-T06 — Avvio, pausa e arresto

Stato: `WAITING_FOR_PREVIOUS_TASKS`
Risultato: controllo singolo e continuo sono non bloccanti e hanno ciclo di vita deterministico.
Dipendenza: `GUI-U-E2-T05 = DONE`.
Componenti ammessi: runner/worker condiviso, coda eventi, controller Home, fake lenti, test di concorrenza.
Esclusioni: servizi reali, nuove azioni operative, processo Windows residente.
Condizione di blocco: il runner esistente non puo` essere controllato senza duplicare logica o lasciare processi orfani.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Il controllo singolo e` non bloccante. | Test con fake lento e verifica reattivita`. | — | `NOT_RUN` |
| Il controllo continuo e` non bloccante. | Test start con fake worker. | — | `NOT_RUN` |
| La pausa e` funzionante. | Test stop e stato finale. | — | `NOT_RUN` |
| Non puo` partire un doppio processo. | Test doppio start concorrente. | — | `NOT_RUN` |
| Non resta un processo orfano alla chiusura. | Test close con worker attivo. | — | `NOT_RUN` |

### GATE U-H2 — Collaudo umano del percorso verticale

Stato iniziale: `WAITING_FOR_PREVIOUS_TASKS`.

Codex non puo` dichiararlo `PASS`.

Scenario umano:

1. avvio GUI;
2. selezione Limbo;
3. configurazione di due caselle;
4. chiusura e riapertura;
5. visualizzazione Home;
6. controllo manuale;
7. avvio;
8. pausa.

Condizioni:

- nessun terminale;
- nessuna modifica manuale di file;
- nessuna documentazione tecnica necessaria;
- nessun termine vietato visibile.

GUI-U-E3 non puo` iniziare prima del `PASS` esplicito.

## GUI-U-E3 — Completamento e distribuzione

Stato: `WAITING_FOR_PREVIOUS_TASKS`.

### GUI-U-E3-T01 — Attivita` e problemi

Stato: `WAITING_FOR_PREVIOUS_TASKS`
Risultato: attivita` e problemi sono leggibili e orientati all'azione.
Dipendenza: `GATE U-H2 = PASS`.
Componenti ammessi: vista attivita`, proiezione eventi, filtri, dettaglio tecnico separato, test UI.
Esclusioni: nuovi eventi di dominio, modifica pipeline, dati reali.
Condizione di blocco: gli eventi esistenti non possono essere tradotti senza esporre dati sensibili o dettagli tecnici nella vista ordinaria.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste una tabella attivita`. | Test UI su colonne e righe sintetiche. | — | `NOT_RUN` |
| Esistono filtri essenziali. | Test combinazioni casella, esito e data. | — | `NOT_RUN` |
| Non compare JSON. | Test sulle stringhe e celle visibili. | — | `NOT_RUN` |
| Ogni problema contiene un'azione consigliata. | Test su catalogo errori rappresentativo. | — | `NOT_RUN` |
| I dettagli tecnici sono separati. | Test UI su pannello avanzato chiuso per default. | — | `NOT_RUN` |

### GUI-U-E3-T02 — Impostazioni essenziali

Stato: `WAITING_FOR_PREVIOUS_TASKS`
Risultato: le preferenze ordinarie sono modificabili senza esporre parametri tecnici.
Dipendenza: `GUI-U-E3-T01 = DONE`.
Componenti ammessi: vista impostazioni, modello configurazione condiviso, servizi avvio/chiusura, test UI.
Esclusioni: configurazione Bucoliche, manutenzione, installer.
Condizione di blocco: una preferenza non ha una fonte autorevole unica o richiede modifica manuale di file.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| E` configurabile il Limbo. | Test UI e persistenza con directory temporanea. | — | `NOT_RUN` |
| E` configurabile l'intervallo. | Test validazione e round-trip. | — | `NOT_RUN` |
| E` configurabile l'avvio automatico. | Test con adapter Windows fake. | — | `NOT_RUN` |
| E` configurabile il comportamento alla chiusura. | Test controller sui comportamenti ammessi. | — | `NOT_RUN` |
| I parametri tecnici sono confinati alle impostazioni avanzate. | Test sulle stringhe visibili di default. | — | `NOT_RUN` |

### GUI-U-E3-T03 — Bucoliche e avvio Windows

Stato: `WAITING_FOR_PREVIOUS_TASKS`
Risultato: Bucoliche e avvio automatico sono configurabili tramite percorsi guidati e stati comprensibili.
Dipendenza: `GUI-U-E3-T02 = DONE`.
Componenti ammessi: servizi Bucoliche e Task Scheduler condivisi, viste guidate, adapter fake, test UI.
Esclusioni: servizi Google reali, credenziali reali, nuove architetture residenti.
Condizione di blocco: un'azione non possiede un servizio applicativo stabile e testabile senza accesso reale.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Bucoliche e` attivabile e disattivabile. | Test UI e persistenza. | — | `NOT_RUN` |
| Il collegamento Google e` guidato. | Test del percorso con adapter fake. | — | `NOT_RUN` |
| Il registro e` verificabile. | Test read-only con fake client. | — | `NOT_RUN` |
| Avvio automatico installabile e rimovibile. | Test con adapter Task Scheduler fake. | — | `NOT_RUN` |
| Lo stato e` comprensibile. | Test dei messaggi per stati ed errori noti. | — | `NOT_RUN` |

### GUI-U-E3-T04 — Manutenzione avanzata

Stato: `WAITING_FOR_PREVIOUS_TASKS`
Risultato: `Caronte Manutenzione` espone le operazioni tecniche tramite una nuova
presentazione protetta, separata dall'implementazione legacy.
Dipendenza: `GUI-U-E3-T03 = DONE`.
Componenti ammessi: `maintenance_gui`, nuova presentazione manutenzione, servizi backup/integrita`/diagnostica/reset, test fake.
Esclusioni: import o nuove funzioni in `gui`/`gui_*`, cancellazioni non confermate, dati reali.
Condizione di blocco: un'operazione distruttiva non offre backup, conferma o risultato verificabile.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| Esiste il backup. | Test su directory temporanea e contenuto prodotto. | — | `NOT_RUN` |
| Esiste la verifica integrita`. | Test su stato valido e corrotto sintetico. | — | `NOT_RUN` |
| Esiste il report diagnostico. | Test di redazione e contenuti minimi. | — | `NOT_RUN` |
| Il reset e` protetto. | Test su conferma, annullamento e backup. | — | `NOT_RUN` |
| `Caronte Manutenzione` usa la nuova presentazione senza import legacy. | Test UI, import e inventario della build. | — | `NOT_RUN` |

### GUI-U-E3-T05 — Build autonoma

Stato: `WAITING_FOR_PREVIOUS_TASKS`
Risultato: una build one-folder riproducibile avvia Caronte senza ambiente di sviluppo.
Dipendenza: `GUI-U-E3-T04 = DONE`.
Componenti ammessi: configurazione build, risorse, entry point utente, smoke della build, documentazione di build.
Esclusioni: installer, pubblicazione, firma codice, modifica Apps Script.
Condizione di blocco: la build richiede repository, runtime esterno o file non dichiarati.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| La build one-folder e` riproducibile. | Due build pulite con inventario equivalente. | — | `NOT_RUN` |
| Il runtime e` incluso. | Avvio su ambiente di test senza runtime installato. | — | `NOT_RUN` |
| Non e` richiesto un venv. | Smoke da shell priva dell'ambiente di sviluppo. | — | `NOT_RUN` |
| Non e` richiesto il repository. | Smoke dopo copia della sola cartella build. | — | `NOT_RUN` |
| L'avvio avviene da `Caronte.exe`. | Test di processo e titolo finestra. | — | `NOT_RUN` |

### GUI-U-E3-T06 — Installer Windows

Stato: `WAITING_FOR_PREVIOUS_TASKS`
Risultato: Caronte e` installabile e disinstallabile con dati separati dal programma.
Dipendenza: `GUI-U-E3-T05 = DONE`.
Componenti ammessi: configurazione installer, artefatto build, collegamento Start, test su VM/ambiente isolato.
Esclusioni: distribuzione pubblica, firma commerciale, aggiornamento automatico.
Condizione di blocco: l'installer richiede privilegi o dipendenze non dichiarati, oppure mescola dati utente e file programma.

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |
| L'installer funziona. | Installazione pulita su VM Windows. | — | `NOT_RUN` |
| Esiste il collegamento nel menu Start. | Verifica automatica/manuale del collegamento. | — | `NOT_RUN` |
| La directory dati e` separata. | Verifica path dopo primo avvio. | — | `NOT_RUN` |
| La disinstallazione funziona. | Verifica rimozione programma e policy dati. | — | `NOT_RUN` |
| Il wizard parte alla prima apertura. | Avvio su profilo utente nuovo. | — | `NOT_RUN` |

### GATE U-H3 — Collaudo umano di distribuzione

Stato iniziale: `WAITING_FOR_PREVIOUS_TASKS`.

Codex non puo` dichiararlo `PASS`.

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
