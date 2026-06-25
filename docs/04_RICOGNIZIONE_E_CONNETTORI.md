# Ricognizione e connettori

Questo documento serve per la revisione con Federico e Luca. Non sceglie una soluzione: raccoglie domande e confronta le opzioni principali.

## Scheda ricognizione

### Posta

- Gmail?
- Outlook?
- Entrambe?
- Client desktop?
- Client mobile?
- Caselle condivise?
- Etichette o cartelle usate davvero dagli utenti?
- Chi puo' autorizzare accessi o automazioni?

### Documenti

- Google Drive?
- Shared Drive?
- Server?
- SharePoint?
- OneDrive?
- Backup?
- Permessi?
- Sincronizzazione locale attiva?
- Cartelle cliente gia' esistenti?

### Dispositivi

- Windows?
- macOS?
- iOS?
- Android?
- Browser prevalente?
- Restrizioni aziendali sui dispositivi?

### CRM

- VTEnext attivo?
- Moduli usati?
- Formazione fatta?
- Webhook disponibili?
- API disponibili?
- Quale oggetto rappresenta una pratica?
- Quale oggetto rappresenta un cliente/sito?

### Sicurezza

- Antivirus?
- Sandbox allegati?
- Gestione identita'?
- MFA?
- Ruoli?
- Log?
- Policy su allegati e macro?

### Responsabilita'

- Chi mantiene il sistema?
- Chi approva nuove funzioni?
- Chi autorizza utenti?
- Chi gestisce incidenti?
- Chi decide quando una funzione passa da test a produzione?

## Comparazione connettori

| Connettore | Vantaggi | Limiti | Complessita' | Quando usarlo |
|---|---|---|---|---|
| GmailApp mono-utente | Semplice, gia' funzionante | Solo casella esecutore, poco scalabile | Bassa | MVP e test personali |
| Trigger Apps Script personali | Ogni utente lavora nel proprio contesto | Installazione e manutenzione per utente | Media | Piccolo team, governance leggera |
| Workspace Studio Flow | Approccio visuale e vicino agli utenti | Limiti su etichette, allegati, disponibilita' feature | Media | Da prototipare se disponibile nel dominio |
| Gmail API + DWD | Centralizzato, adatto al multi-mailbox Google | Richiede admin, service account, sicurezza forte | Alta | Se Google Workspace resta centrale |
| Local IMAP / Caronte Locale | Multi-casella, provider-agnostico, meno lock-in Google | Installazione locale, credenziali IMAP/app password, gestione manutenzione | Media | v1.1 e pilota multi-casella |
| Upload manuale Virgilio | Massimo controllo umano, indipendente dalla posta | Meno automatico | Bassa | Fallback sempre disponibile |
| Outlook / Power Automate | Integrato in Microsoft 365 | Dipende da licenze e governance tenant | Media | Se il team usa Outlook/Microsoft |
| Microsoft Graph | Potente e centralizzato | Richiede competenze cloud e permessi admin | Alta | Se Microsoft 365 diventa piattaforma principale |

## Glossario

| Termine | Significato |
|---|---|
| Virgilio | Nome del progetto e dell'interfaccia guida per l'utente |
| Caronte | Componente operativo che esegue le azioni deterministiche |
| Limbo | Area temporanea dove arrivano allegati in attesa di verifica/assegnazione |
| Bucoliche | Registro operativo su Google Sheets |
| Empireo | Archivio documentale principale nel prototipo Drive |
| Adamo | Template cartelle usato dal prototipo |
| Minosse | Futuro classificatore AI |
| Dante | Futuro ghostwriter AI |
| Ulisse | Futuro estrattore dati |
| Cerbero | Futuro guardiano scadenze |
| Beatrice | Possibile modulo amministrativo/fatturazione futuro |
| Connettore | Componente che porta input da posta, upload o altri sistemi verso Virgilio |
| Archivio definitivo | Sistema scelto per conservazione documentale stabile |
| Coda | Area o stato temporaneo prima dell'archiviazione finale |
| MVP | Versione minima funzionante per validare il flusso |
| Revisione umana | Conferma esplicita di un tecnico prima di un'azione critica |
| Rollback | Procedura per tornare a uno stato precedente sicuro |
