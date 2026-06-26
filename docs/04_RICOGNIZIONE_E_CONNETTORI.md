# Ricognizione e connettori

Questo documento serve per orientare le scelte tecniche. La ricognizione iniziale resta utile, ma gli ultimi sviluppi hanno chiarito la direzione: per la v1.1 il connettore prioritario e' **Local IMAP / Caronte Locale**.

## Esito della ricognizione

La v1.0 Google Workspace ha validato il flusso, ma ha confermato un limite: GmailApp non gestisce naturalmente piu' caselle, perche' opera nel contesto dell'account esecutore.

Per questo, il multi-casella va affrontato fuori da GmailApp:

```text
Caronte Locale
  -> N caselle IMAP
  -> account_alias obbligatorio
  -> stato locale
  -> ack sulla casella di origine
```

## Scheda ricognizione aggiornata

### Posta

Da raccogliere per ogni casella pilota:

- indirizzo email;
- `account_alias`;
- provider;
- host IMAP;
- porta IMAP;
- username;
- variabile ambiente per password/app password;
- cartella/label di ingresso;
- cartella/label di completamento;
- cartella/label errore;
- MFA/app password disponibili;
- consenso esplicito dell'utente.

### Documenti

Da chiarire:

- Drive Desktop e' installato?
- Esiste una cartella condivisa di test?
- Serve compatibilita' con OneDrive/SharePoint?
- Esistono gia' cartelle cliente/pratica?
- Chi puo' scrivere nella cartella finale?
- Serve NAS/server locale?
- Come si fa backup?

### Dispositivi

Da chiarire:

- Windows o macOS?
- PC sempre acceso o uso manuale?
- antivirus locale disponibile?
- permessi installazione Python/servizio?
- restrizioni aziendali?
- uso da mobile solo come comando via email oppure anche gestione?

### Responsabilita'

Da decidere:

- chi configura le caselle;
- chi conserva le app password;
- chi aggiorna Caronte Locale;
- chi controlla errori;
- chi autorizza nuovi utenti;
- chi decide passaggio da pilota a produzione.

## Comparazione connettori

| Connettore | Vantaggi | Limiti | Complessita' | Quando usarlo |
|---|---|---|---|---|
| GmailApp mono-utente | Semplice, gia' funzionante | Solo casella esecutore, non multi-mailbox | Bassa | MVP v1.0 e test personali |
| Trigger Apps Script personali | Ogni utente lavora nel proprio contesto Google | Installazione/manutenzione per utente | Media | Piccolo team solo Google |
| Gmail API + DWD | Multi-mailbox Google centralizzato | Richiede admin Workspace e sicurezza forte | Alta | Solo se Google Workspace resta piattaforma centrale |
| Workspace Studio Flow | Vicino agli utenti, visuale | Limiti su label/allegati e maturita' feature | Media | Da valutare, non priorita' |
| Local IMAP / Caronte Locale | Multi-casella, provider-agnostico, meno lock-in | Installazione locale, app password, manutenzione | Media | Priorita' v1.1 |
| Upload manuale Virgilio | Massimo controllo umano | Meno automatico | Bassa | Fallback sempre valido |
| Power Automate / Outlook | Integrato in Microsoft 365 | Dipende da licenze e tenant | Media | Se il team usa Microsoft |
| Microsoft Graph | Potente e centralizzato | Richiede competenze cloud/admin | Alta | Fase futura se Microsoft diventa centrale |
| rclone/storage sync | Provider-agnostico per file | Configurazione extra | Media | Futuro storage adapter |

## Scelta operativa v1.1

Per la v1.1 la scelta e':

```text
Local IMAP / Caronte Locale come connettore prioritario.
Apps Script come adapter Google opzionale.
```

Questa scelta non elimina Google Workspace. Lo ridimensiona:

- Drive puo' restare archivio o storage adapter;
- Bucoliche puo' restare registro leggibile;
- Apps Script puo' restare ponte Google;
- ma la logica multi-casella deve stare nel motore locale.

## Dati minimi per il pilota multi-casella

Per ogni casella:

```yaml
account_alias: marco_sigmapiu
email: marco@sigmapiu.it
provider_hint: gmail_workspace
imap_host: imap.gmail.com
imap_port: 993
username_env: VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME
password_env: VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD
input_folder: Virgilio/da-traghettare
done_folder: Virgilio/traghettate
error_folder: Virgilio/errore
enabled: true
```

Le credenziali reali non devono mai entrare in Git.

## Glossario aggiornato

| Termine | Significato |
|---|---|
| Virgilio | Interfaccia/progetto guida per l'utente |
| Caronte Locale | Motore operativo locale multi-casella |
| Apps Script adapter | Ponte opzionale verso Google Workspace |
| Limbo | Area temporanea/staging, non archivio definitivo |
| Quarantena locale | Area controllata prima di staging o archiviazione |
| Bucoliche | Registro ispezionabile su Google Sheets, adapter opzionale |
| SQLite | Registro operativo primario locale |
| Empireo | Archivio documentale principale nel prototipo Drive |
| Storage adapter | Componente che scrive su cartelle locali, Drive, SharePoint o altro |
| Notifier adapter | Componente che invia notifiche senza bloccare lo stato primario |
| Ack IMAP | Chiusura/spostamento/label della mail sulla casella di origine |
| Account alias | Nome stabile interno per distinguere le caselle |
| Manifest | JSON metadati allegato, usato per tracciabilita' e idempotenza |
