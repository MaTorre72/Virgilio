# Decisioni e rischi

Questo documento raccoglie decisioni aperte, decisioni architetturali gia' assunte nel prototipo, incongruenze e rischi prioritari. Dove manca una scelta condivisa viene indicato **DA DECIDERE**.

## Decisioni aperte

| ID | Tema | Domanda | Opzioni | Decisione | Responsabile | Scadenza | Stato |
|---|---|---|---|---|---|---|---|
| D01 | Archivio definitivo | Dove devono vivere i documenti finali? | Drive, Shared Drive, SharePoint, server, ibrido | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D02 | Suite principale | Google Workspace, Microsoft 365 o ibrido? | Google, Microsoft, ibrido | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D03 | Multi-mailbox | Come leggere piu' caselle? | Trigger personali, Workspace Studio, Gmail API + DWD, Graph, manuale | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D04 | Limbo | Il Limbo e' staging o quarantena? | Staging semplice, quarantena controllata, doppio stato | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D05 | Database futuro | Bucoliche basta o serve altro? | Sheets, database relazionale, CRM, data warehouse | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D06 | VTEnext | Che ruolo ha nel flusso? | Solo anagrafica, commesse, workflow, nessuno per ora | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D07 | Notifiche | Quale canale e' ufficiale? | Chat, Telegram, email, CRM, combinazione | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D08 | Allegati malevoli | Quali file sono ammessi e come verificarli? | Allowlist, quarantena, antivirus, sandbox, blocco archivi | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D09 | Provider AI | Quale provider usare per funzioni AI? | OpenAI, Google, Microsoft, locale, nessuno | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D10 | Privacy e GDPR | Quali dati possono uscire verso servizi AI/API? | Dati fittizi, anonimizzati, reali con DPA, esclusi | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D11 | Costi API | Come stimare e controllare i costi? | Budget mensile, log chiamate, approvazione manuale | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D12 | Manutenzione | Chi mantiene il sistema? | Interno, consulente, misto | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D13 | Ownership | Chi decide priorita' e rilasci? | Responsabile tecnico, gruppo revisione, direzione | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |
| D14 | Metriche pilota | Come misurare il successo? | Tempo risparmiato, errori evitati, pratiche aperte, soddisfazione | DA DECIDERE | DA DECIDERE | DA DECIDERE | Aperta |

## Decisioni architetturali registrate

### ADR-001 - Google Workspace come prototipo

**Contesto:** la v1.0 e' stata costruita rapidamente dentro Google Workspace usando Apps Script, Drive, Sheets, Gmail, Chat e Telegram.

**Decisione:** Google Workspace viene usato come ambiente rapido di prototipazione, non come vincolo definitivo dell'architettura.

**Motivazione:** l'ambiente era disponibile, consente iterazione rapida e permette di validare il flusso operativo prima di scegliere una piattaforma stabile.

**Conseguenze:** le scelte future devono restare aperte a Microsoft 365, architetture ibride, connettori esterni o altri archivi.

**Limiti:** Apps Script e GmailApp non risolvono in modo naturale il multi-mailbox e non sono una base sufficiente per automazioni enterprise senza ulteriori controlli.

**Alternative considerate:** Cloud Run, Gmail API con Domain-Wide Delegation, Workspace Studio Flow, Microsoft Graph, Power Automate, upload manuale.

### ADR-002 - AI con revisione umana

**Contesto:** il progetto prevede possibili agenti AI per classificazione, estrazione, ghostwriting e controllo scadenze.

**Decisione:** le funzioni AI producono suggerimenti, classificazioni, estrazioni o bozze. Nessuna azione critica viene eseguita senza revisione umana.

**Motivazione:** le pratiche ambientali contengono dati sensibili, documenti tecnici e responsabilita' operative. L'AI deve ridurre attrito, non sostituire il giudizio tecnico.

**Conseguenze:** ogni agente deve avere logging, conferma umana, test su dati fittizi o anonimizzati e possibilita' di rollback.

**Limiti:** l'automazione completa viene rinviata. Accuratezza, costi e privacy vanno misurati prima dell'uso reale.

**Alternative considerate:** AI solo consultiva, AI disabilitata, AI autonoma sopra soglie di confidenza. L'opzione autonoma non viene adottata.

### ADR-003 - Bucoliche registro non database

**Contesto:** Bucoliche e' un Google Sheet usato per registrare operazioni, errori e metadati del prototipo.

**Decisione:** Bucoliche viene mantenuto come registro operativo temporaneo del prototipo. Non viene considerato database definitivo.

**Motivazione:** Sheets e' semplice da ispezionare e adatto a un MVP, ma non offre le garanzie di un database applicativo per concorrenza, schema evolutivo, audit e integrazioni complesse.

**Conseguenze:** le evoluzioni devono evitare di costruire dipendenze irreversibili su Bucoliche.

**Limiti:** lo schema potra' cambiare; eventuali dati storici vanno migrati solo dopo una decisione esplicita.

**Alternative considerate:** database relazionale, CRM, data warehouse, archivio su file. Nessuna alternativa e' scelta in questa fase.

## Decisioni implicite rilevate

| ID | Decisione implicita | Dove emerge | Nota |
|---|---|---|---|
| I01 | Il gesto intenzionale dell'utente e' centrale | README e flusso Gmail con etichetta | Da preservare anche in v1.1 |
| I02 | Le notifiche non bloccano l'operazione principale | `notifiche.gs` e chiamate try/catch | Da documentare nei criteri operativi |
| I03 | Bucoliche tollera errori senza bloccare Drive | `bucoliche.gs` | Utile nel prototipo, da rivalutare in produzione |
| I04 | Il Limbo e' temporaneo ma non formalmente quarantena | `caronte.gs` | Rischio da discutere |
| I05 | Il matching Limbo -> pratica e' temporale | `caronte.gs` | Potenziale errore in multi-utente |

## Incongruenze rilevate

| ID | Tema | Descrizione | Impatto | Stato |
|---|---|---|---|---|
| C01 | Nome progetto | Alcuni testi storici usano "Virgilio / Caronte"; il progetto va chiamato solo "Virgilio". | Chiarezza comunicativa | Segnalata |
| C02 | Multi-utente | La configurazione puo' elencare piu' utenti, ma GmailApp legge solo la casella dell'esecutore. | Funzionale | Segnalata |
| C03 | Limbo | Il termine puo' far pensare a quarantena, ma i controlli attuali sono solo filtri semplici. | Sicurezza | Segnalata |
| C04 | Bucoliche | La documentazione puo' descriverlo come ricco registro dati, ma non va trattato come database definitivo. | Architettura | Segnalata |

## Rischi prioritari

| Priorita' | Rischio | Descrizione | Mitigazione proposta |
|---|---|---|---|
| Alta | Allegati malevoli | Un file salvato su Drive non e' automaticamente sicuro. | Allowlist, quarantena, permessi, niente sync automatica |
| Alta | Multi-mailbox non risolto | GmailApp non impersona altri utenti. | Valutare connettori prima del deploy condiviso |
| Alta | Spostamento errato dal Limbo | Matching temporale puo' spostare file nella pratica sbagliata. | Conferma manuale o metadati di associazione |
| Media | Segreti e webhook | Token e webhook vanno tenuti fuori dal codice. | PropertiesService, Secret Manager, rotazione |
| Media | Dipendenza da Sheets | Bucoliche potrebbe diventare un database di fatto. | Limitare uso a registro e pianificare scelta futura |
| Media | AI prematura | Uso su documenti reali senza policy privacy. | DPA, test fittizi, revisione umana |
