# Architettura Caronte Desktop utente

> Documento storico assorbito in
> `docs/ARCHITETTURA_UNIFICATA.md`. I confini ancora validi sono mantenuti nel
> documento canonico; stati `target` e percorsi futuri qui restano storici.

## Scopo e stato

Questo documento fissa i confini della nuova applicazione desktop `Caronte`.
Descrive l'architettura target, non dichiara ancora implementati `user_app`, i
nuovi servizi applicativi o il packaging Windows. La classificazione puntuale dei
moduli esistenti e` demandata a `GUI-U-E0-T03`.

La GUI utente e` un adapter di presentazione dei casi d'uso di Caronte. Non e` un
catalogo grafico dei comandi della CLI. L'implementazione GUI legacy (`gui`,
`gui_*`) e` abbandonata. `Caronte Manutenzione` resta invece un'applicazione
target, con una nuova presentazione separata che non importa il legacy.

## Regole di dipendenza

Le dipendenze ammesse procedono in una sola direzione:

```text
user_app ---------+
maintenance_gui --+--> servizi applicativi --> dominio/porte --> adapter locali
CLI ---------------+             |
                                  +--> supervisore del processo in background
```

- `virgilio_connector.user_app` non importa `maintenance_gui`, `gui` o alcun
  modulo `gui_*` della GUI tecnica. Non importa neppure il registro delle nove
  vecchie tab o i relativi descrittori di azione.
- la nuova presentazione `maintenance_gui` non importa `gui` o `gui_*`; espone
  soltanto attivita` tecniche previste tramite servizi applicativi condivisi;
- i servizi applicativi non importano toolkit grafici, `user_app`,
  `maintenance_gui` o `__main__`;
- la CLI e le due nuove presentazioni traducono input/output dei rispettivi
  canali, senza
  contenere logica operativa duplicata;
- i moduli legacy `gui` e `gui_*` non sono consumer target dei servizi e non
  sono importati, avviati o impacchettati dalle nuove presentazioni;
- il supervisore in background non importa toolkit grafici e pubblica solo
  stato ed eventi tipizzati.

Il controllo automatico previsto per la fondazione di `user_app` analizzera`
gli import del package e fallira` se trova un riferimento a
`maintenance_gui`, `gui` o `gui_*`. Un secondo controllo sugli import dei
servizi condivisi fallira` se trova un riferimento a una delle presentazioni o
a `__main__`.

## Layout target del package

Il layout seguente assegna una sola sede a ogni responsabilita`. I nomi dei
moduli applicativi sono target; `GUI-U-E0-T03` stabilira` per ciascun modulo
esistente se puo` essere riusato, adattato o deve restare tecnico.

```text
virgilio_connector/
  user_app/
    __init__.py          # entry point della sola applicazione utente
    app.py               # composizione e ciclo della finestra Caronte
    navigation.py        # routing tra primo avvio e Home
    views/               # viste e presenter senza logica operativa
  maintenance_gui.py     # entry point target della nuova Caronte Manutenzione
  maintenance_views/     # nuova presentazione tecnica separata dal legacy
  gui.py / gui_*.py      # implementazione legacy abbandonata
  application/
    configuration.py     # configurazione strutturale tramite porta dedicata
    accounts.py          # casi d'uso delle caselle e verifica separata
    operations.py        # controllo singolo, avvio, pausa e stato
    activity.py          # proiezione leggibile delle attivita`
    maintenance.py       # casi d'uso espliciti di manutenzione
    windows_startup.py   # casi d'uso dell'avvio automatico
  background.py          # supervisore indipendente dal toolkit grafico
  ports.py               # contratti verso filesystem, credenziali, mail e registro
  ...                    # dominio e adapter locali esistenti da classificare in E0-T03
  __main__.py            # adapter CLI e dispatch, non servizio applicativo
```

Il packaging e` un consumer esterno del package: costruisce `Caronte.exe`
puntando all'entry point di `user_app` e, se previsto, costruisce
`CaronteManutenzione.exe` dalla nuova presentazione `maintenance_gui`. I moduli
legacy `gui` e `gui_*` non entrano nelle build. Ricette, icone, installer e build
restano fuori da questo task.

## Componenti e responsabilita`

| Componente | Responsabilita` esclusiva | Non possiede |
| --- | --- | --- |
| `user_app` | flusso utente, navigazione, widget, testo comprensibile e traduzione degli eventi applicativi | regole operative, persistenza, accesso mail, registro tecnico o nove tab legacy |
| `maintenance_gui` / `maintenance_views` | nuova suite tecnica, navigazione e presentazione delle sole attivita` di manutenzione previste | logica operativa, widget legacy o flusso ordinario di `user_app` |
| `gui` / `gui_*` | nessuna responsabilita` target; implementazione legacy abbandonata | nuove presentazioni, servizi condivisi o packaging |
| servizi `application` | casi d'uso, validazione, coordinamento delle porte e risultati tipizzati condivisi | widget, parsing di argomenti CLI o dettagli del processo figlio |
| `background` | ciclo di vita start/stop, esclusione dei doppi avvii, arresto alla chiusura ed eventi di stato | widget, testi tecnici visibili o regole di dominio |
| dominio e porte | modelli, invarianti e contratti indipendenti dai canali | filesystem, rete o toolkit concreti |
| adapter locali | implementazione di filesystem, archivio credenziali, mail, Registro e avvio Windows | navigazione o decisioni di presentazione |
| CLI / `__main__` | parsing, dispatch, formato dell'output e codici di ritorno | implementazione dei casi d'uso |
| packaging | composizione dell'eseguibile e risorse di distribuzione | logica applicativa o configurazione utente |

## Contratti dei servizi condivisi

I contratti espongono dati strutturati ed errori tipizzati; non restituiscono
output CLI grezzo, stack trace o stringhe dipendenti dal toolkit.

| Contratto | Operazioni minime | Consumer |
| --- | --- | --- |
| `ConfigurationService` | rilevare configurazione valida, caricare, validare e salvare atomicamente il modello | `user_app`, CLI, `maintenance_gui` |
| `AccountService` | elencare, creare, modificare, disabilitare, rimuovere e verificare una casella | `user_app`, CLI, `maintenance_gui` |
| `OperationService` | controllo singolo, lettura stato, avvio e pausa del ciclo operativo | `user_app`, CLI, `background`, `maintenance_gui` |
| `ActivityService` | leggere una proiezione filtrabile e redatta delle attivita` | `user_app`, CLI, `maintenance_gui` |
| `MaintenanceService` | backup, integrita`, ripristino controllato, import/export e pulizia | `user_app` solo per casi approvati, CLI, `maintenance_gui` |
| `WindowsStartupService` | piano, installazione, stato e rimozione dell'avvio automatico | `user_app`, CLI, `maintenance_gui` |
| `BackgroundSupervisor` | `start`, `pause`, `close`, stato corrente e coda eventi tipizzati | `user_app`, `maintenance_gui`; usa `OperationService` |

Ogni consumer applica la propria presentazione allo stesso risultato. Per
esempio, un errore di collegamento tipizzato diventa testo azionabile in
`user_app`, dettaglio tecnico nella nuova `maintenance_gui` e output/return code
nella CLI, senza rieseguire o duplicare la regola operativa.

## Entry point definitive

| Superficie | Nome definitivo | Target | Stato |
| --- | --- | --- | --- |
| prodotto desktop | `Caronte` | `virgilio_connector.user_app:launch_user_app` | target da implementare |
| comando prodotto | `user-gui` | dispatch CLI verso `launch_user_app` | target da aggiungere |
| eseguibile prodotto | `Caronte.exe` | stesso entry point di `user_app` | packaging futuro |
| applicazione tecnica | `Caronte Manutenzione` | nuova presentazione `virgilio_connector.maintenance_gui:launch_gui` | target da implementare separando il legacy |
| comando tecnico | `maintenance-gui` | dispatch CLI verso la nuova `launch_gui` | nome target confermato |
| eseguibile tecnico | `CaronteManutenzione.exe` | nuova presentazione `maintenance_gui` | eventuale packaging futuro |
| automazione e assistenza | `virgilio` | `virgilio_connector.__main__:main` | presente |

`local_connector/pyproject.toml` mantiene oggi il solo console script
`virgilio`. L'aggiunta del subcommand `user-gui` appartiene alla fondazione
della shell; la creazione degli eseguibili appartiene al packaging. Il comando
`maintenance-gui` conserva il nome target, ma dovra` avviare la nuova
presentazione separata. L'alias `gui` e l'implementazione `gui`/`gui_*` sono
legacy abbandonato e destinati a rimozione tramite un task separato. Nessuna
superficie target cambia nome senza decisione umana.

## Percorso verticale minimo

1. L'utente apre `Caronte`; `user_app` chiede a `ConfigurationService` se esiste
   una configurazione valida.
2. Se manca, il primo avvio raccoglie la Cartella Limbo e configura due caselle
   tramite `AccountService`, una alla volta, senza esporre dettagli tecnici.
3. La conferma finale valida e salva tramite i servizi condivisi. Solo un esito
   valido porta alla Home; un errore resta nel passo pertinente con indicazione
   azionabile.
4. La Home legge stato e riepilogo da `OperationService` e mostra Caronte fermo,
   le due caselle attive e le azioni primarie.
5. `Avvia` delega a `BackgroundSupervisor`, che garantisce una sola esecuzione e
   pubblica gli aggiornamenti consumati dalla Home senza bloccare la finestra.
6. `Pausa` chiede al supervisore un arresto controllato; la Home torna allo stato
   fermo. La chiusura della finestra applica lo stesso contratto e non lascia
   processi orfani.

Il percorso dimostra l'asse completo primo avvio -> due caselle -> Home ->
avvio/pausa. Registro condiviso, attivita`, manutenzione estesa e packaging non
sono necessari per la prima fetta verticale e restano nei task dedicati.
