# Decisioni e rischi

Questo documento raccoglie decisioni aperte, decisioni architetturali assunte e rischi prioritari del progetto Virgilio.

## Decisioni aperte

| ID | Tema | Domanda | Opzioni | Decisione | Stato |
|---|---|---|---|---|---|
| D01 | Archivio definitivo | Dove devono vivere i documenti finali? | Drive, Shared Drive, SharePoint, server, ibrido | DA DECIDERE | Aperta |
| D02 | Suite principale | Google Workspace, Microsoft 365 o ibrido? | Google, Microsoft, ibrido, local-first | Local-first per v1.1, suite da decidere | Parziale |
| D03 | Multi-mailbox | Come leggere piu' caselle? | GmailApp, API, DWD, Graph, IMAP locale | Caronte Locale via IMAP | Decisa per v1.1 |
| D04 | Limbo | Il Limbo e' staging o quarantena? | Staging, quarantena, doppio stato | Quarantena locale + staging controllato | Parziale |
| D05 | Database futuro | Bucoliche basta o serve altro? | Sheets, SQLite, CRM, DB relazionale | SQLite locale primario per v1.1 | Parziale |
| D06 | VTEnext | Che ruolo ha nel flusso? | Anagrafica, commesse, workflow, nessuno | DA DECIDERE | Aperta |
| D07 | Notifiche | Quale canale e' ufficiale? | Chat, Telegram, email, CRM, combinazione | Adapter opzionali | Parziale |
| D08 | Allegati malevoli | Quali file sono ammessi e come verificarli? | Allowlist, quarantena, antivirus, sandbox | Allowlist + scanner locale per pilota | Parziale |
| D09 | Provider AI | Quale provider usare? | OpenAI, Google, Microsoft, locale, nessuno | Nessuno per pilota v1.1 | Sospesa |
| D10 | Privacy e GDPR | Quali dati possono uscire verso servizi AI/API? | Fittizi, anonimizzati, reali con DPA, esclusi | Nessuna AI su dati reali nel pilota | Parziale |
| D11 | Costi API | Come controllare i costi? | Budget, log, approvazione | Limitare automazioni e token | Aperta |
| D12 | Manutenzione | Chi mantiene il sistema? | Interno, consulente, misto | DA DECIDERE | Aperta |
| D13 | Ownership | Chi decide priorita' e rilasci? | Responsabile tecnico, gruppo revisione, direzione | DA DECIDERE | Aperta |
| D14 | Metriche pilota | Come misurare il successo? | Tempo, errori, pratiche, soddisfazione | DA DECIDERE | Aperta |

## Decisioni architetturali registrate

### ADR-001 - Google Workspace come prototipo

**Contesto:** la v1.0 e' stata costruita rapidamente dentro Google Workspace usando Apps Script, Drive, Sheets, Gmail, Chat e Telegram.

**Decisione:** Google Workspace viene usato come ambiente rapido di prototipazione, non come vincolo definitivo dell'architettura.

**Motivazione:** l'ambiente era disponibile, consente iterazione rapida e permette di validare il flusso operativo.

**Conseguenze:** le scelte future devono restare aperte a Microsoft 365, architetture ibride, connettori locali o altri archivi.

**Limiti:** Apps Script e GmailApp non risolvono il multi-mailbox. GmailApp opera sulla casella dell'account esecutore.

### ADR-002 - AI con revisione umana

**Contesto:** il progetto prevede possibili agenti AI per classificazione, estrazione, ghostwriting e controllo scadenze.

**Decisione:** le funzioni AI producono suggerimenti, classificazioni, estrazioni o bozze. Nessuna azione critica viene eseguita senza revisione umana.

**Motivazione:** le pratiche ambientali contengono dati sensibili, documenti tecnici e responsabilita' operative.

**Conseguenze:** ogni agente deve avere logging, conferma umana, test su dati fittizi o anonimizzati e possibilita' di rollback.

**Stato:** AI fuori dal pilota v1.1.

### ADR-003 - Bucoliche registro non database

**Contesto:** Bucoliche e' un Google Sheet usato per registrare operazioni, errori e metadati del prototipo.

**Decisione:** Bucoliche viene mantenuto come registro ispezionabile/output adapter. Non viene considerato database definitivo.

**Motivazione:** Sheets e' semplice da leggere, ma non offre le garanzie di un database applicativo.

**Conseguenze:** le evoluzioni devono evitare dipendenze irreversibili da Bucoliche.

### ADR-004 - Caronte Locale come nucleo local-first

**Contesto:** gli sviluppi sul Local IMAP Connector hanno introdotto lettura IMAP read-only, quarantena locale, scansione opzionale, SQLite, manifest JSON, staging Drive Desktop, verifica cloud e intake test.

**Decisione:** Caronte Locale diventa il nucleo operativo multi-casella. Apps Script resta adapter Google opzionale.

**Motivazione:** un nucleo locale e provider-agnostico riduce il lock-in Google e rende piu' naturale la gestione di caselle IMAP diverse.

**Conseguenze:** la roadmap v1.1 deve dare priorita' a multi-account IMAP, ack locale, SQLite come fonte primaria, adapter Bucoliche e storage adapter.

**Limiti:** aumentano responsabilita' locali di installazione, configurazione credenziali IMAP/app password, manutenzione e supervisione.

### ADR-005 - Ack sulla casella di origine

**Contesto:** P4 e' stato chiuso usando Apps Script/GmailApp solo sulla casella che lo script poteva leggere.

**Decisione:** nel modello v1.1 l'ack deve essere eseguito da Caronte Locale sulla stessa casella IMAP da cui la mail e' stata letta.

**Motivazione:** solo cosi' il sistema puo' diventare multi-casella e indipendente dal dominio Google Workspace.

**Conseguenze:** l'ack deve diventare una strategia IMAP configurabile e idempotente.

## Decisioni implicite da preservare

| ID | Decisione implicita | Nota |
|---|---|---|
| I01 | Il gesto intenzionale dell'utente e' centrale | L'utente marca/sposta una mail da lavorare |
| I02 | Le notifiche non bloccano l'operazione principale | Devono restare adapter opzionali |
| I03 | Bucoliche e' ispezionabile ma non primario | SQLite deve tenere lo stato vero |
| I04 | Il Limbo non basta come quarantena | Serve quarantena locale controllata |
| I05 | Il matching temporale e' fragile | Servono manifest, ID e stato esplicito |

## Incongruenze corrette o da correggere

| ID | Tema | Descrizione | Stato |
|---|---|---|---|
| C01 | Nome progetto | Virgilio e Caronte vanno distinti per ruolo, non trattati come sinonimi | Da mantenere chiaro |
| C02 | Multi-utente | GmailApp non vede caselle diverse dall'esecutore | Confermato |
| C03 | Limbo | Drive non e' quarantena completa | Mitigato con quarantena locale |
| C04 | Bucoliche | Non deve diventare database di fatto | Confermato |
| C05 | Apps Script | Non deve restare nucleo multi-casella | Da correggere in roadmap/codice futuro |

## Rischi prioritari

| Priorita' | Rischio | Descrizione | Mitigazione |
|---|---|---|---|
| Alta | Allegati malevoli | Un file salvato o sincronizzato non e' automaticamente sicuro | Allowlist, quarantena locale, scanner, no apertura automatica |
| Alta | Multi-mailbox finto | Configurare piu' caselle ma chiudere tramite GmailApp non risolve il problema | Ack IMAP locale |
| Alta | Duplicazioni | Retry o sincronizzazioni possono produrre righe doppie | Idempotenza su `attachment_id` e `sha256` |
| Alta | Spostamento errato file | File assegnati alla pratica sbagliata | Manifest, stato, conferma e storage adapter |
| Media | Segreti e credenziali | Password/app password IMAP o webhook nel repository | Variabili ambiente, `.env` escluso, rotazione |
| Media | Dipendenza da Drive Desktop | Sync asincrona e non garantita istantaneamente | Stato separato: `staged_local_drive` != `cloud_visible` |
| Media | Manutenzione locale | Installazione e aggiornamenti su PC utenti | Procedura semplice e checklist |
| Media | AI prematura | Uso AI su dati reali senza policy | Esclusa dal pilota v1.1 |
