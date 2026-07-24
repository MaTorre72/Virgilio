# Collaudo umano Caronte

Questo documento e` il riferimento obbligatorio per tutti i collaudi umani
successivi della GUI utente. Codex prepara build, evidenze e checklist, ma non
compila l'esito umano, non dichiara `PASS` e non supera un gate non approvato.

## Identificazione obbligatoria

Un collaudo e` valido solo se registra:

- data e ora;
- nome del collaudatore;
- sistema operativo;
- scala schermo Windows (`100%`, `125%` o altro valore dichiarato);
- risoluzione schermo;
- nome esatto e SHA-256 dell'installer;
- versione, commit completo e build ID;
- stato iniziale del PC;
- presenza o assenza di installazione e configurazione precedenti.

## Preparazione obbligatoria

1. Chiudere tutte le istanze di Caronte.
2. Disinstallare la versione precedente e verificare che la cartella programma
   precedente non esista piu.
3. Scegliere e annotare `INSTALLAZIONE_PULITA` (senza configurazione precedente)
   oppure `AGGIORNAMENTO_CON_DATI` (configurazione conservata).
4. Calcolare lo SHA-256 dell'installer e confrontarlo con il manifest esterno.
5. Installare il pacchetto.
6. Eseguire `Caronte.exe --build-info` e confrontare versione, commit e build ID
   con il manifest.
7. Aprire `Informazioni su Caronte` e confrontare versione, commit abbreviato e
   build ID.

Una sola divergenza interrompe il collaudo: registrare `INVALID_BUILD`, non
valutare la GUI e non aprire task UX.

## Scheda identificativa vuota

| Campo | Valore umano |
| ----- | ------------ |
| Data e ora | |
| Collaudatore | |
| Sistema operativo | |
| Scala Windows | |
| Risoluzione | |
| Scenario installazione | |
| Stato iniziale PC | |
| Installazione precedente presente | |
| Configurazione precedente presente | |
| Nome installer | |
| SHA-256 installer | |
| Versione | |
| Commit completo | |
| Build ID | |

## GUI-U-R02 - Prototipo visuale completo

Stato storico: `SUPERSEDED_BY_R3` dopo il `FAIL` del demo del 2026-07-23.
Questa checklist non viene ripetuta sul demo. Tutti gli scenari seguenti sono
vincolanti e vengono verificati una sola volta sul percorso operativo reale
insieme al collaudo R3.

Il prototipo usa dati sintetici e comprende Benvenuto, scelta Limbo, Caselle,
Riepilogo finale e Home. Le prove visuali devono essere eseguite sulla build
reale installata.

| Scenario | Verifiche obbligatorie | Esito umano | Evidenza/note |
| -------- | ---------------------- | ------------ | -------------- |
| `H-R02-01` Avvio e orientamento | Una finestra principale; Caronte e scopo immediati; azione iniziale evidente; nessuna istruzione esterna, console o finestra tecnica. | | |
| `H-R02-02` Navigazione wizard | Passaggio corrente e totale riconoscibili; Continua/Indietro funzionano; dati conservati; nessun pulsante morto o punto senza azione. | | |
| `H-R02-03` Limbo | Spiegazione in una frase; selettore cartella; percorso leggibile; azione primaria evidente; errore vicino al campo; nessun ID Drive, YAML, `.env` o percorso tecnico. | | |
| `H-R02-04` Caselle | Elenco distinto dal form dedicato; nome, indirizzo, tipo e stato; Gmail/Workspace comprensibile e prioritario; altro provider secondario; host/porta solo avanzati; nessuna azione ambigua; seconda casella evidente. | | |
| `H-R02-05` Riepilogo | Limbo, caselle e stati; elementi incompleti con azione correttiva; azione primaria `Completa configurazione`; schermata autonoma. | | |
| `H-R02-06` Home | Stato generale, caselle attive, ultimo controllo, prossima azione, attivita recenti, problemi, azione principale e Impostazioni con gerarchia leggibile. | | |
| `H-R02-07` Leggibilita | A 100% e 125%: nessun taglio, sovrapposizione o controllo fuori finestra; azioni principali senza scroll; gerarchia/spaziature coerenti; minimo 960x640 e resize funzionale. | | |
| `H-R02-08` Linguaggio | Assenti Python, venv, CLI, YAML, `.env`, doctor, pilot, dry-run, watch, staging, ack, manifest, SQLite, exit code, variabili, stack trace e path repository; ogni errore spiega problema e azione. | | |

Le evidenze storiche R02 restano conservate. Le nuove evidenze appartengono al
fascicolo R3 della build operativa; non si produce una nuova build demo.

## GUI-U-R03 - Collegamento dei servizi

Il collaudo R3 e` unico: esegue prima gli scenari `H-R02-01`--`H-R02-08` sul
percorso reale e poi gli scenari di collegamento seguenti, senza duplicare passi
o evidenze comuni.

| Scenario | Verifiche obbligatorie | Esito umano | Evidenza/note |
| -------- | ---------------------- | ------------ | -------------- |
| `H-R03-01` Limbo reale | Selezione, validazione, salvataggio, ritorno, riapertura, persistenza e modifica da Impostazioni. | | |
| `H-R03-02` Prima casella | Google: accesso browser, ritorno e riscontro senza password ordinaria. IMAP: email/password/host/porta, verifica read-only ed esito comprensibile. | `PASS` | Conferma umana esplicita del 2026-07-24 sulla build `8241325`, ID `7dcae8b2-5bd2-47b6-9c89-f53b4cf4c1ff`, dopo reinstallazione della build corretta. I due `FAIL` precedenti restano evidenza storica. |
| `H-R03-03` Seconda casella | Credenziale distinta, aggiunta, modifica, disattivazione, riattivazione, rimozione e persistenza. | `PASS` | Conferma umana esplicita del 2026-07-24 sulla stessa build R03-R03 installata. Il prossimo scenario e` `H-R03-04`. |
| `H-R03-04` Feedback | La verifica casella integrata nei flussi di collegamento (`H-R03-02`/`H-R03-03`), Controlla ora, Avvia e Pausa mostrano avvio immediato, stato in corso, esito, errore azionabile e registrazione in Attivita e problemi. | `PASS` | Conferma umana esplicita del 2026-07-24 sulla build R03-R03. Tre screenshot mostrano controllo in corso, ultimo controllo aggiornato, avvio periodico, pausa riuscita e registrazioni coerenti in Attivita; nessuna console, stack trace o termine tecnico esposto. |
| `H-R03-05` Chiusura/riapertura | Chiusura, eventuale icona, nessuna console/processo duplicato, riapertura, persistenza e stato coerente. | `PASS` | Conferma umana esplicita del 2026-07-24 sulla build R03-R03 installata. Il prossimo scenario e` `H-R03-06`. |
| `H-R03-06` Automatico | Attivazione/conferma/stato, disattivazione, persistenza e assenza di finestre o percorsi tecnici. | `PASS` | Conferma umana esplicita del 2026-07-24 sulla build `eaf05fd`, ID `0c40a31d-ee7a-4d8c-9f0d-5ff795fb5b39`: nessun UAC, privilegio, console o finestra tecnica; messaggio, stato e pulsante corretti; stato attivo persistito dopo riapertura e nuovo accesso a Windows; disattivazione persistita dopo ulteriore riapertura. Il `FAIL` precedente sulla build R03-R03 resta storico. |

R03 diventa `DONE` solo dopo conferma umana esplicita. In caso di fallimento si
registrano scenario, passaggio, screenshot, atteso e osservato; si propone un
numero finito di correttivi e si attende approvazione prima di svilupparli.

## GUI-U-R04 - Collaudo finale

Eseguire su PC o profilo Windows senza Python utilizzabile dall'utente:

1. verificare hash e build-info; installare e avviare dal menu Start;
2. completare primo avvio, Limbo e due caselle;
3. chiudere/riaprire e verificare persistenza;
4. eseguire controllo manuale, avvio continuo, pausa e verifica attivita;
5. attivare il controllo automatico, riavviare la sessione o simulare in modo
   equivalente, verificare lo stato e disattivare;
6. aprire Impostazioni e Informazioni su Caronte;
7. disinstallare e verificare rimozione programma e policy di conservazione dati.

Il collaudo avviene senza terminale, modifiche manuali di file/YAML/`.env`, avvio
di Python o consultazione della documentazione tecnica.

## Esiti e regole di giudizio

Esiti ammessi: `PASS`, `FAIL`, `NOT_TESTED`, `BLOCKED_BY_ENVIRONMENT`,
`INVALID_BUILD`.

Un gate e` `PASS` solo se tutti gli scenari obbligatori sono `PASS`, nessuno e`
`FAIL` o `INVALID_BUILD`, gli eventuali `NOT_TESTED` sono solo facoltativi e
installer, hash, commit e build ID sono registrati. Codex non compila l'esito
umano, non trasforma `WAITING_HUMAN_REVIEW` in `PASS`, non deduce accettazione
dai test e non prosegue oltre un gate non approvato.

## Protocollo in caso di FAIL

Non modificare subito il codice. Consolidare prima le evidenze:

| Scenario | Passaggio | Atteso | Osservato | Gravita | Evidenza |
| -------- | --------- | ------ | --------- | ------- | -------- |
| | | | | | |

Classificare ogni voce come difetto funzionale, difetto visuale, problema di
build, installazione, ambiente o requisito ambiguo. Proporre al massimo cinque
task, ciascuno con risultato osservabile, file ammessi, prova automatica e prova
umana, e attendere approvazione prima di modificare il codice.
