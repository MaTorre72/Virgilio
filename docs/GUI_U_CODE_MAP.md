# Mappa del codice riutilizzabile per Caronte

## Scopo

Questa mappa classifica l'implementazione GUI legacy rispetto alle nuove
presentazioni di `Caronte` e `Caronte Manutenzione`. La classificazione non
autorizza import diretti dai moduli `gui` o `gui_*`: le regole di dipendenza di
`docs/GUI_U_ARCHITETTURA.md` restano vincolanti.

Le categorie usate sono:

- `RIUTILIZZABILE`: indipendente dalla presentazione e utilizzabile tramite un
  servizio o una porta condivisa;
- `ADATTABILE`: contiene comportamento utile, ma deve essere estratto o separato
  dalla presentazione tecnica;
- `LEGACY_ABBANDONATO`: non ha destinazione nel prodotto o negli strumenti
  supportati e resta soltanto fino a una rimozione dedicata;
- `NON_IMPORTABILE`: il disegno corrente viola i confini della GUI utente e non
  puo` essere usato direttamente.

## Inventario completo dei moduli GUI esistenti

Inventario verificato contro i file `gui*.py` e `maintenance_gui.py` del package.

| Modulo | Responsabilita` attuale verificata | Test esistenti | Classificazione | Destinazione |
| --- | --- | --- | --- | --- |
| `maintenance_gui.py` | entry point target che oggi riesporta la GUI legacy | `test_gui.py` | `ADATTABILE` | conserva identita` e comando di `Caronte Manutenzione`, ma deve comporre una nuova presentazione senza importare `gui` o `gui_*` |
| `gui.py` | finestra Tk tecnica, nove tab, registro azioni, costruzione argomenti ed esecuzione comandi | `test_gui.py` | `LEGACY_ABBANDONATO` | nessun widget, tab o registro passa alle nuove presentazioni; rimuovere dopo l'estrazione dei soli comportamenti utili |
| `gui_config.py` | modello account/storage, lettura e scrittura coordinata dei file locali, credenziali e preferenze runtime | `test_gui_config.py` | `ADATTABILE` | separazione in `application.configuration`, porta credenziali e preferenze; nessun import diretto da `user_app` |
| `gui_accounts.py` | casi d'uso CRUD delle caselle e verifica IMAP read-only | `test_gui_accounts.py` | `ADATTABILE` | estrazione in `application.accounts` sopra porte configurazione, credenziali e mail |
| `gui_activity.py` | proiezione leggibile, redazione e filtri degli eventi locali | `test_gui_activity.py` | `ADATTABILE` | estrazione in `application.activity`; testi e azioni restano responsabilita` della presentazione utente |
| `gui_home.py` | snapshot e transizioni visibili della Home, oggi accoppiati agli eventi del runner tecnico | `test_gui_home.py` | `ADATTABILE` | view model in `user_app` alimentato da risultati tipizzati di `OperationService` e `BackgroundSupervisor` |
| `gui_runner.py` | possesso di un processo CLI figlio, raccolta di stdout/stderr e ciclo start/stop | `test_gui_runner.py` | `NON_IMPORTABILE` | sostituzione con `background.py` e `OperationService`; sono riutilizzabili solo le invarianti di singola esecuzione e arresto deterministico |
| `gui_wizard.py` | stato dei passi, validazione e persistenza del primo avvio nello stesso oggetto | `test_gui_wizard.py` | `ADATTABILE` | navigazione in `user_app`, validazione e salvataggio tramite `ConfigurationService` e `AccountService` |

Non esiste un modulo GUI classificato `RIUTILIZZABILE` direttamente: il divieto
di import dei moduli legacy e la commistione residua con presentazione o formati
locali richiedono estrazione. Restano invece riutilizzabili dietro le nuove porte
i modelli e gli adapter non grafici gia` presenti, tra cui `multi_account`,
`imap_readonly`, `traceability`, `state_db`, `windows_task`, `orchestrator` e
`pipeline`, nei limiti indicati dalla matrice seguente.

## Destinazione dei servizi necessari

| Servizio o porta target | Codice esistente di partenza | Destinazione | Lacuna da chiudere |
| --- | --- | --- | --- |
| `ApplicationPaths` | percorsi distribuiti tra configurazione e CLI | condiviso, fondazione | risoluzione Windows indipendente da repository e cwd (`GUI-U-E1-T01`) |
| `ConfigurationService` | `gui_config`, loader e modelli di `multi_account` | `application.configuration` condiviso | modello strutturale unico senza dipendenze GUI (`GUI-U-E1-T02`) |
| `CredentialStore` | valori locali gestiti dentro `gui_config` | porta condivisa piu` adapter Windows | contratto astratto e backend sicuro (`GUI-U-E1-T03`, `GUI-U-E1-T04`) |
| `AccountService` | `gui_accounts`, `multi_account`, `imap_readonly` | `application.accounts` condiviso | risultati tipizzati e separazione da file e credenziali (`GUI-U-E2-T03`, `GUI-U-E2-T04`) |
| `OperationService` | dispatch in `__main__`, `orchestrator`, `pipeline`, `multi_account` | `application.operations` condiviso | facciata di casi d'uso senza parsing o output CLI (`GUI-U-E2-T06`) |
| `BackgroundSupervisor` | invarianti di `gui_runner` | `background` condiviso | esecuzione diretta dei servizi, eventi tipizzati e nessun processo CLI figlio (`GUI-U-E2-T06`) |
| `ActivityService` | `gui_activity`, `traceability`, `state_db` | `application.activity` condiviso | porta di lettura e proiezione indipendente dai widget (`GUI-U-E3-T01`) |
| `WindowsStartupService` | `windows_task` e dispatch CLI | `application.windows_startup` condiviso | casi d'uso tipizzati e testi presentati dal consumer (`GUI-U-E3-T03`) |
| `MaintenanceService` | funzioni oggi esposte da CLI e nove tab tecniche | `application.maintenance` condiviso | facciata protetta; `user_app` espone solo casi approvati (`GUI-U-E3-T04`) |

CLI, `user_app` e la nuova presentazione `maintenance_gui` sono consumer dei
servizi condivisi. L'implementazione legacy `gui`/`gui_*` non lo e`. Flusso,
navigazione, widget e testi finali appartengono alla rispettiva presentazione;
registro delle nove tab e relativi controller non hanno una destinazione target.
Argomenti, output e codici di ritorno restano responsabilita` della CLI.

## Lacune applicative finite

- Fondazioni E1: percorsi Windows iniettabili; modello di configurazione unico;
  porta credenziali; adapter credenziali Windows (`GUI-U-E1-T01..T04`).
- Percorso verticale E2: shell `user_app` con controllo import; schermate reali
  del wizard; configurazione ordinaria di una e poi due caselle; Home minima;
  operazioni e supervisore non bloccanti (`GUI-U-E2-T01..T06`).
- Completamento E3: attivita` e problemi; preferenze essenziali; Bucoliche e
  avvio Windows guidati; nuova presentazione di manutenzione protetta; build e installer autonomi
  (`GUI-U-E3-T01..T06`).

L'elenco e` chiuso sui task E1-E3 gia` definiti. Eventuali miglioramenti non
necessari a questi risultati devono diventare task separati e non modificano la
classificazione corrente.

## Attivita` utente, non comandi trasformati in pulsanti

| Attivita` dell'utente | Composizione prevista | Superfici tecniche escluse |
| --- | --- | --- |
| completare il primo avvio | navigazione `user_app`, configurazione e caselle | `init-config`, argomenti e file locali visibili |
| controllare o mettere in pausa Caronte | Home, `OperationService`, supervisore | `pilot`, `watch`, stdout/stderr e codici di ritorno |
| gestire le caselle | schermate dedicate e `AccountService` | alias tecnici, nomi di variabili e comandi CRUD |
| capire cosa e` accaduto | vista Attivita` e `ActivityService` | schema del registro, JSON e percorsi locali |
| cambiare preferenze o avvio automatico | percorsi guidati dei servizi dedicati | parametri CLI e dettagli del task Windows |
| svolgere manutenzione approvata | percorso protetto e `MaintenanceService` | registro delle nove tab e catalogo dei comandi |

La presenza di un comando CLI non crea quindi un'azione o un pulsante nella GUI
utente. Ogni controllo visibile deve derivare da un'attivita` prevista nei task
E2-E3 e consumare un servizio applicativo.

## Primo task di fondazione

`GUI-U-E1-T01 - Percorsi applicativi Windows` e` la prima unita` eseguibile dopo
il gate umano. La scheda contiene risultato concreto, cinque criteri binari con
prova prevista, dipendenza `GATE U-H1 = PASS`, componenti ammessi, esclusioni e
condizione di blocco. E` quindi completa secondo la Definition of Done, ma resta
non avviabile finche` il gate non riceve un `PASS` umano esplicito.
