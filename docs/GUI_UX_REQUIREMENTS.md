# Requisiti UX GUI Caronte locale

## Stato e obiettivo

Il collaudo manuale del 2026-07-14 e` negativo. La GUI corrente dimostra il
collegamento tecnico con la CLI, ma non consente a un utente medio di installare,
configurare e usare Caronte locale senza terminale. `V114-T17` resta quindi
`IN_PROGRESS - Collaudo UX non superato`.

La GUI finale deve partire dalle attivita` dell'utente. CLI e GUI condividono gli
stessi servizi applicativi; la GUI puo` invocarli direttamente quando il processo
CLI renderebbe l'interfaccia bloccante o fragile. La logica operativa non va duplicata.

## Evidenze del riesame

- Il pannello globale `Parametri azioni` mescola campi relativi ad azioni diverse.
- Esiste un solo insieme di campi account e non esistono password, CRUD multi-account
  o persistenza coordinata di YAML e valori locali.
- Sono esposti termini e controlli tecnici (`Config YAML`, Python, staging, dry-run,
  cicli, force, doctor e pilot) e molte azioni disabilitate con motivazioni interne.
- Il monitoraggio continuo usa una chiamata sincrona e non conserva un processo
  arrestabile: puo` bloccare la GUI e non offre uno stop funzionante.
- L'output ordinario e` l'output CLI, non uno stato o una cronologia orientati all'utente.

## Modello unico di configurazione

Per l'utente esiste una sola configurazione. L'implementazione puo` mantenere due
file locali, entrambi gestiti esclusivamente dai servizi applicativi e dalla GUI:

| Dato | Fonte autorevole | Regola |
|---|---|---|
| account, alias stabile, email, provider, host, porta, cartelle, stato, limiti e completamento | `accounts.local.yaml` | un record per casella; `account_alias` e` la chiave stabile interna |
| Cartella Limbo | `storage.staging_dir` in `accounts.local.yaml` | unico valore operativo; in GUI si chiama `Cartella Limbo` |
| username e password per account | `.env` locale ignorato da Git | nomi generati dall'alias e referenziati dal YAML; valori mai scritti nel YAML o nei log |
| cartella dati locali e parametri locali non strutturali | `.env` locale ignorato da Git | gestiti dalla GUI; nessuna modifica manuale richiesta |
| Bucoliche e modalita` di autenticazione | sezione `bucoliche` nel YAML | ID e path sensibili/variabili restano nel file locale tramite riferimenti stabili |

`VIRGILIO_IMAP_ACCOUNT_1_ALIAS` e `VIRGILIO_IMAP_ACCOUNT_2_ALIAS` sono doppioni
rispetto ad `account_alias` e devono essere rimossi o migrati. Analogamente,
`VIRGILIO_LIMBO_LOCAL_SYNC_DIR` non deve competere con `storage.staging_dir` e deve
essere rimosso o migrato. Il servizio deve aggiornare record esistenti, generare
nomi di variabili stabili, impedire alias duplicati e salvare i due file in modo
coerente e recuperabile.

## Primo avvio guidato

Quando manca una configurazione valida, mostrare quattro passaggi:

1. **Cartelle**: cartella dati locali e Cartella Limbo, con verifica di esistenza,
   accesso, scrittura e creazione controllata.
2. **Caselle email**: tabella e finestra semplice/avanzata per almeno due caselle,
   con credenziali distinte, attivazione e verifica IMAP read-only per singolo account.
3. **Registro condiviso**: scelta iniziale Bucoliche si/no; se si`, ID Spreadsheet,
   autenticazione, file OAuth quando richiesto, collegamento Google e verifica automatica
   di `Bucoliche_Eventi`, `Bucoliche_Stato` e `Bucoliche_Conflitti`.
4. **Verifica finale**: riepilogo leggibile, problemi da correggere, salvataggio e
   azione `Avvia Caronte`; include cartelle, account, test per casella, scanner e
   stato del Registro condiviso.

Per Gmail e Google Workspace precompilare host, porta e cartelle consigliate. Il
provider generico consente valori personalizzati. La parte avanzata resta richiudibile.
La tabella account mostra nome, indirizzo, provider, collegamento e stato attivo.
La parte semplice contiene nome, provider, indirizzo/username, password con mostra/nascondi
e stato; quella avanzata contiene host, porta, cartelle input/completate/errori, limite
messaggi e opzione comprensibile per segnare come elaborata.

## Interfaccia ordinaria

- **Home**: stato attivo/fermo/errore, ultima e prossima verifica, caselle attive,
  contatori e problemi; azioni primarie `Controlla ora`, `Avvia` e `Ferma`.
- **Caselle email**: elenco, aggiunta, modifica, abilita/disabilita, rimozione e test
  separato, senza nomi di variabili ambiente.
- **Attivita`**: data/ora Europe/Rome, casella, messaggio, allegato, attivita`, esito
  e problema, con filtri; niente JSON grezzo nella vista ordinaria.
- **Impostazioni**: cartelle, intervallo, scanner, Registro condiviso, avvio Windows
  e sole opzioni pertinenti.
- **Manutenzione**: backup, integrita`, reset con backup, export/import senza segreti,
  pulizia controllata e diagnostica avanzata; conferma esplicita per azioni distruttive.

## Monitoraggio e linguaggio

Il controllo singolo e quello continuo sono distinti. Il continuo usa un worker o
processo gestito, impedisce doppi avvii, conserva stato e riferimento, aggiorna la
GUI senza bloccarla, si arresta su richiesta o chiusura e non lascia orfani.

Nella vista ordinaria non mostrare doctor, pilot, dry-run, staging, ack, manifest,
SQLite, PRAGMA, CLI mancante, nomi YAML/env, Python, force o max cycles. Tradurre
gli errori indicando cosa non funziona, perche` conta e cosa deve fare l'utente.
Le funzioni centrali mancanti vanno implementate prima di essere mostrate; quelle
secondarie restano nascoste o nella sola diagnostica avanzata.

## Collaudo finale

Il task potra` chiudersi solo dopo un collaudo da configurazione assente con almeno
due caselle differenti, persistenza dopo riapertura, test read-only separati, prova
senza modifiche remote, avvio e arresto, attivita` leggibile, automazione Windows e
manutenzione essenziale, senza terminale e senza editing manuale di YAML o `.env`.
