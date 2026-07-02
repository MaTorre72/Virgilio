# Architettura unificata Virgilio

Virgilio ha due ingressi tecnici e un solo flusso operativo.

Frase guida: "Virgilio ha due ingressi tecnici e un solo flusso operativo."

## Flusso unico

Acquisizione -> Limbo -> Da archiviare -> Form -> Pratica finale -> Registro

## Profili operativi

### Google-only

- Ingresso tecnico: `GmailApp`.
- Usa il Limbo condiviso come prima area operativa visibile in Google Drive.
- Crea una riga in `Da archiviare` quando il documento e` pronto per la decisione umana.
- Rimane il profilo semplice per chi lavora solo in Google Workspace.

### Local connector

- Ingresso tecnico: `IMAP locale`.
- Passa prima da `Quarantena`, poi da `Scan`, poi nel Limbo.
- Produce gli stessi oggetti operativi del profilo Google-only.
- Rimane il profilo piu` sicuro per piu` caselle, piu` utenti e per la scansione prima del Limbo.

## Lessico ufficiale

- Quarantena: cartella locale non condivisa, prima della scansione.
- Limbo: cartella Google Drive condivisa dei documenti acquisiti ma non ancora archiviati.
- Da archiviare: coda operativa umana dei documenti nel Limbo.
- Registro: unico registro di audit.
- Form: interfaccia umana Virgilio.
- Pratica finale: cartella della commessa/pratica, con archiviazione in `02_corrispondenza` o cartella equivalente.

## Ruoli

### Registro

Il Registro e` l'unico audit ufficiale. Contiene gli eventi rilevanti, gli esiti e le tracce operative necessarie a ricostruire cosa e` successo.

### Da archiviare

`Da archiviare` e` la coda di lavoro corrente. Non e` un archivio storico e non sostituisce il Registro. Serve a rappresentare le pratiche che richiedono una decisione o un completamento umano.

## Cosa resta tecnico o legacy

- `staging` resta un termine tecnico storico e non deve comparire nella UX.
- `Bucoliche_Eventi`, `Bucoliche_Stato` e `Bucoliche_Conflitti` restano supporti tecnici o di compatibilita`.
- `Virgilio_Inbox` resta il nome tecnico della coda operativa; nella UX si chiama `Da archiviare`.
- `manifest`, `fingerprint` e `SQLite` restano dettagli diagnostici.

## Cosa non fare

- Non introdurre un secondo Limbo operativo.
- Non creare nuovi registri produttivi separati dal Registro.
- Non usare `Bucoliche_*` come inbox o come coda utente.
- Non mandare byte, base64 o path locali ad Apps Script.
- Non riscrivere il form per separare i due profili.
- Non sostituire Apps Script con Python.
- Non esporre dettagli macchina inutili nella UX normale.

## Nota operativa

Gli sviluppi gia` fatti su Google Apps Script e sul local connector vanno riconciliati, non cancellati. Le parti tecniche storiche si preservano finche` servono alla compatibilita` o alla diagnostica.
