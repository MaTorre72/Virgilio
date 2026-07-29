# Roadmap Virgilio 1.1

## Come leggere questo documento

La roadmap originale ha definito la direzione **local-first** con le fasi A-H.
Questa versione conserva esattamente quel lessico e distingue:

- obiettivo originario;
- risultato effettivamente consegnato;
- prova disponibile nella release 1.1;
- eventuale limite che rimane dopo il completamento.

Non e` un backlog attivo: la release 1.1.0 e` ufficiale e le fasi A-H sono
chiuse. Le proposte successive richiedono nuovi task e nuove decisioni.

## Direzione architetturale consolidata

```text
Virgilio = interfaccia, guida, supervisione
Caronte Locale = motore operativo locale multi-casella
Apps Script = adapter Google
SQLite = stato tecnico locale
Bucoliche / Registro = audit cloud umano
```

La roadmap iniziale descriveva Apps Script come adapter Google opzionale e
SQLite come fonte primaria locale. La realizzazione finale precisa il confine:
SQLite e` primario per lo stato tecnico del connettore, mentre il Registro
Bucoliche rimane l'audit umano condiviso; Apps Script resta necessario nel
profilo Google e nel tratto condiviso form/Drive/Da archiviare della 1.1.

## Quadro complessivo

| Fase | Nome originale | Stato 1.1 | Evidenza principale |
| --- | --- | --- | --- |
| A | Consolidamento | completata | release 1.1.0, fonti canoniche e repository ripulito |
| B | Multi-account IMAP locale | completata | configurazione multi-account e isolamento errori |
| C | Quarantena e staging per account | completata | identita`, scan, manifest e staging idempotente |
| D | Ack IMAP locale | completata | post-condizioni e completamento sulla casella di origine |
| E | Registro SQLite e Bucoliche adapter | completata | stato locale persistente e Registro unico append-only |
| F | Storage adapter cartelle pratica | completata per il target 1.1 | Drive Desktop verso Limbo e Apps Script verso pratica |
| G | Notifiche adapter | completata per i canali 1.1 | Chat e Telegram non bloccanti |
| H | Pilota 2 utenti | completata | collaudo umano PASS del 28 luglio 2026 |

## Fase A - Consolidamento

### Obiettivo originario

Portare sulla linea 1.1 soltanto i blocchi stabili, riducendo branch,
duplicazioni documentali e ambiguita` tra prototipo Google e connettore locale.

### Risultato

- versione unica `1.1.0` e tag pubblicato;
- `main` aggiornata alla release dopo revisione umana;
- sorgente Apps Script canonica in `apps_script/src/`;
- package locale con dipendenze in `pyproject.toml`;
- entry point Caronte, manutenzione e CLI dichiarati;
- documentazione corrente separata per utente, tecnica e sviluppo;
- file storici recuperabili da Git, non esposti come fonti concorrenti.

### Limite residuo

La pulizia documentale non elimina la necessita` di ownership: ogni nuovo
programma deve mantenere un indice unico e archiviare la storia in Git, non in
nuove cartelle parallele.

## Fase B - Multi-account IMAP locale

### Obiettivo originario

Configurare piu` caselle con `account_alias` obbligatorio, lettura iniziale
read-only, log separati e isolamento degli errori.

### Risultato

- configurazione YAML con piu` account;
- alias univoci e provider hint;
- username/password referenziati tramite variabili ambiente;
- `BODY.PEEK` e nessuna marcatura involontaria;
- errore per account senza blocco delle caselle successive;
- Gmail OAuth Desktop e IMAP generico dietro lo stesso modello.

### Prova

Test unit, contract e integration_offline coprono parsing, isolamento,
connessioni fake e comportamento read-only.

## Fase C - Quarantena e staging per account

### Obiettivo originario

Evitare commistioni e duplicazioni tra caselle, propagando account, identita`
allegato e hash fino allo storage.

### Risultato

- radice di quarantena locale controllata;
- allowlist, limite dimensione e scansione;
- `attachment_id`, fingerprint e SHA-256;
- manifest JSON verificabile;
- namespace e correlazioni per account;
- copia nel Limbo senza overwrite silenzioso;
- distinzione tra staging locale e visibilita` cloud.

### Prova

Fixture sintetiche verificano file ammessi, rifiutati, duplicati, traversal,
collisioni e retry Drive.

## Fase D - Ack IMAP locale

### Obiettivo originario

Chiudere la mail sulla stessa casella da cui e` stata letta, soltanto dopo presa
in carico riuscita, stato coerente, file gestiti e audit aggiornato.

### Risultato

- strategia ack per account;
- aggiunta dell'etichetta/cartella di completamento;
- rimozione della sola etichetta di ingresso;
- verifica della post-condizione;
- niente `DELETE`, `MOVE` o `EXPUNGE`;
- mail multi-allegato conclusa soltanto quando tutti gli allegati sono
  archiviati.

### Prova

Contratti e test di completamento coprono replay, risposta parziale, conflitto e
nessun falso ack.

## Fase E - Registro SQLite e Bucoliche adapter

### Obiettivo originario

Persistenza locale, idempotenza e audit ispezionabile senza trasformare Google
Sheets in un database applicativo.

### Risultato

- `state.db` con messaggi, allegati, tentativi ed eventi;
- migrazioni additive e controllo schema;
- ripresa da errori attraverso transizioni ammesse;
- unico Registro umano nel tab `bucoliche` a 17 colonne;
- append da Google-only e Local connector;
- nessun tab produttivo parallelo per stato o conflitti.

### Chiarimento rispetto alla roadmap iniziale

SQLite e` la fonte dello stato tecnico locale, non la fonte dell'audit umano.
Bucoliche non blocca le operazioni che la policy definisce non critiche, ma la
condizione di completamento continua a richiedere la traccia prevista dal
flusso.

## Fase F - Storage adapter cartelle pratica

### Obiettivo originario

Separare il motore dalla destinazione documentale e consentire una consegna
configurabile.

### Risultato 1.1

- adapter filesystem/Drive Desktop per la consegna locale al Limbo;
- verifica read-only della presenza cloud;
- Apps Script come adapter verso la cartella finale della pratica;
- idempotenza, manifest e conflitto esplicito.

### Fuori perimetro

NAS, OneDrive/SharePoint, rclone e API storage non sono implementazioni
ufficiali della 1.1. Restano possibili adapter futuri, non opzioni gia`
supportate.

## Fase G - Notifiche adapter

### Obiettivo originario

Isolare le notifiche dal nucleo operativo e impedire che diventino fonte
primaria dello stato.

### Risultato 1.1

- Google Chat e Telegram dietro funzioni dedicate;
- fallimento notifica non equivalente a fallimento documentale;
- messaggi derivati dallo stato, non viceversa;
- nessun canale richiesto per eseguire la suite offline.

Email, CRM e altri notifier restano ipotesi future.

## Fase H - Pilota 2 utenti

### Obiettivo originario

Provare due account, allegati innocui, stato coerente, ack locale, assenza di
perdita e rollback documentato.

### Risultato

- baseline funzionale `7e18277`;
- deployment Apps Script `40`;
- reset locale con backup;
- suite offline finale di 548 test;
- build e installer 1.1.0 verificati;
- collaudo umano `PASS` del 28 luglio 2026.

Il PASS appartiene a questa baseline. Modifiche comportamentali future devono
ottenere prove e gate nuovi.

## Decisioni consolidate dalla roadmap

- il multi-casella non viene costruito su GmailApp;
- il gesto intenzionale dell'utente resta l'ingresso del flusso;
- quarantena, Limbo, Da archiviare e pratica finale sono aree diverse;
- SQLite conserva stato tecnico; il Registro conserva audit umano;
- l'ack e` locale e successivo al completamento documentale;
- Apps Script resta adapter Google e il form non viene riscritto;
- storage e notifier sono estensioni tramite porte, non logica duplicata;
- AI e database remoti restano fuori dalla 1.1.

## Direzioni successive, non ancora approvate

Qualunque lavoro successivo deve partire dalle
[decisioni e rischi](DECISIONI_E_RISCHI.md) e diventare un programma separato.
Le aree candidate sono:

1. aggiornamento e migrazione semplificati su piu` postazioni;
2. nuova Caronte Manutenzione completamente separata dal legacy;
3. osservabilita`, backup e recupero piu` guidati;
4. supporto verificato ad altri provider IMAP;
5. storage o notifier aggiuntivi soltanto per casi d'uso confermati;
6. ownership, supporto e ciclo di rilascio formalizzati.

AI, RAG, server web e database remoti non diventano automaticamente parte della
roadmap futura: richiederebbero requisiti, privacy, governance e test propri.
