# Decisioni e rischi dopo la release 1.1

## Scopo

Questo documento aggiorna le decisioni della roadmap originale. Separa cio`
che la 1.1 ha consolidato dai temi che un nuovo programma deve ancora decidere.
Non introduce funzionalita` per semplice aspirazione.

## Decisioni consolidate

### ADR-001 - Google Workspace come prototipo e adapter

La 1.0 ha validato rapidamente il flusso con Apps Script, Drive, Sheets e
GmailApp. Google Workspace resta una parte supportata, ma non definisce il
motore multi-casella. Conseguenza: gli sviluppi Google vivono nell'adapter e non
spostano in Apps Script lo stato tecnico locale.

### ADR-002 - Caronte Locale come nucleo multi-casella

IMAP, quarantena, scan, SQLite, storage e ack sono coordinati localmente.
Conseguenza: configurazione, aggiornamento e protezione del PC diventano
responsabilita` operative esplicite.

### ADR-003 - Due ingressi, un solo flusso

Google-only e Local connector convergono su Limbo, Da archiviare, form, pratica
e Registro. Conseguenza: non si creano una seconda coda o un secondo archivio
per il profilo locale.

### ADR-004 - Ack sulla casella di origine

Il completamento multi-account e` eseguito da Caronte Locale dopo le
post-condizioni. Conseguenza: GmailApp non e` il meccanismo principale di ack e
la strategia IMAP deve essere idempotente.

### ADR-005 - SQLite stato tecnico, Bucoliche audit umano

SQLite conserva ripresa e correlazioni locali; il tab `bucoliche` e` il solo
Registro cloud append-only. Conseguenza: nessuno dei due va trasformato nel
duplicato dell'altro.

### ADR-006 - Decisione umana e form preservato

La scelta della pratica resta umana e il form non viene riscritto. Conseguenza:
eventuali suggerimenti futuri non possono archiviare autonomamente documenti
critici.

### ADR-007 - Adapter per storage e notifiche

Storage e notifier sono separati dal nucleo. Conseguenza: un nuovo provider
deve implementare una porta, mantenere post-condizioni e avere test offline; non
si aggiungono chiamate sparse nei servizi o nella GUI.

### ADR-008 - AI fuori dalla 1.1

AI, RAG, Docling e LiteLLM non appartengono alla baseline. Una loro eventuale
valutazione futura richiede un programma separato con privacy, costi,
tracciabilita`, revisione umana e rollback.

## Decisioni aperte per un programma successivo

| ID | Tema | Decisione necessaria | Non decidere implicitamente con |
| --- | --- | --- | --- |
| O01 | ownership | chi approva release, gestisce incidenti e ruota credenziali | un nuovo script |
| O02 | aggiornamenti | installazione in-place, migrazione stato e rollback | sovrascrittura manuale |
| O03 | manutenzione | perimetro definitivo della nuova GUI Manutenzione | pulsanti che invocano la CLI uno-a-uno |
| O04 | provider IMAP | quali provider e strategie ack sono ufficialmente supportati | esempi non collaudati |
| O05 | storage | se serve davvero un adapter oltre Drive Desktop | elenco di opzioni nella roadmap |
| O06 | notifiche | canale operativo richiesto e politica di errore | preferenza tecnica |
| O07 | conservazione | retention di quarantena, stato e Registro | cancellazioni automatiche non approvate |
| O08 | metriche | tempo, errori, documenti e soddisfazione da misurare | conteggi di test |

## Rischi correnti

| Priorita` | Rischio | Effetto | Mitigazione attuale | Decisione futura |
| --- | --- | --- | --- | --- |
| alta | allegato ostile | compromissione del PC o propagazione nel Drive | quarantena, allowlist, scanner, no apertura | aggiornamento policy e motore scan |
| alta | falsa archiviazione | mail conclusa ma documento non disponibile | macchina a stati e post-condizioni | telemetria e recovery guidato |
| alta | duplicazione | righe o file doppi dopo retry | identita`, hash, manifest e vincoli | test con nuovi adapter |
| alta | credenziali esposte | accesso a caselle o Google | deposito protetto, ignore e redazione | ownership e rotazione |
| media | sync Drive lenta | documento in attesa o retry ripetuti | verifica cloud e backoff limitato | SLA operativo o adapter alternativo |
| media | manutenzione locale | installazioni divergenti | build/installer e diagnostica | aggiornamento centralizzato o procedura |
| media | dipendenza dal deployment GAS | contratto locale/cloud disallineato | baseline e test contract | strategia versionamento deployment |
| media | documentazione divergente | sviluppo sulla fonte sbagliata | indice unico e tre aree | review documentale a ogni contratto |

## Metodo per assumere una nuova decisione

Una ADR successiva deve dichiarare contesto, opzioni reali, decisione,
conseguenze, migrazione, rollback e test. Deve aggiornare architettura e roadmap
nello stesso task; un documento di brainstorming non diventa automaticamente
fonte canonica.
