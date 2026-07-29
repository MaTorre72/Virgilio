# Come contribuire a Virgilio

## Prima di iniziare

Virgilio non e` un progetto greenfield: la 1.1 e` una baseline collaudata. Ogni
modifica deve dichiarare quale comportamento cambia o quale regressione
corregge, e deve preservare i confini descritti nella documentazione tecnica.

Leggi nell'ordine:

1. [`AGENTS.md`](../../AGENTS.md);
2. `CODEX_STATE.md`;
3. `NEXT_CODEX_TASKS.md`;
4. la sola sezione pertinente di `DEV_BACKLOG.md`, se richiamata;
5. i file tecnici e i test della superficie interessata.

## Scegliere la superficie

| Se il task riguarda | Profilo e sorgenti |
| --- | --- |
| GmailApp, form, Drive, fogli o deploy | Google-only, `apps_script/src/` |
| IMAP, quarantena, scan, SQLite, Drive Desktop o app desktop | Local connector, `local_connector/src/` |
| esperienza Caronte | `user_app/` sopra i servizi `application/` |
| manutenzione | `maintenance_gui.py` e servizi `application/maintenance.py` |
| automazione e diagnostica | CLI sopra gli stessi servizi applicativi |

Non trasformare automaticamente un comando CLI in un pulsante. Prima si
definisce l'attivita` dell'utente, poi si riusa il servizio condiviso.

## Task chiudibile

Un task deve avere:

- un risultato osservabile;
- non piu` di cinque criteri binari;
- componenti ammessi ed esclusioni;
- test proporzionati;
- una condizione di blocco verificabile;
- nessuna voce generica come "rifinire" o "migliorare".

Una run esegue un solo task e crea al massimo un commit atomico. Se il task non
e` chiudibile, il codice parziale non utile va rimosso e si registra una sola
causa con una sola azione necessaria.

## Ciclo Git sicuro

1. verificare branch e working tree;
2. eseguire `fetch --prune` e confrontare HEAD, upstream e merge-base;
3. usare soltanto fast-forward quando il remoto e` avanti e HEAD ne e`
   antenato;
4. modificare il minimo insieme coerente di file;
5. eseguire test e review del diff;
6. controllare file vietati e segreti;
7. creare un solo commit;
8. rifare fetch e pushare senza forzare soltanto se l'upstream e` invariato.

Non modificare o unire `main` durante un task di sviluppo e non usare reset
distruttivi.

## Test

Quando si tocca codice, aggiungere prima il test mirato. Per percorso locale o
governance eseguire poi:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1
```

La suite usa fixture sintetiche. Mail, Google, Drive, credenziali e notifiche
reali sono sempre fuori dai test. Le regole dettagliate sono in
[Sicurezza e test](../tecnica/SICUREZZA_E_TEST.md).

## Compatibilita` e contratti

Prima di refactoring o rimozioni controllare:

- entry point package, CLI e GUI;
- schema dei payload Caronte;
- stati SQLite e migrazioni additive;
- contratto metadata-only Apps Script;
- nomi tecnici `Virgilio_Inbox` e `bucoliche`;
- build e installer;
- riferimenti documentali e script di governance.

Una rimozione richiede prova di non raggiungibilita`, recuperabilita` Git e test
mirato. Il semplice fatto che un file sembri vecchio non e` sufficiente.

## Checklist prima della review

- criteri del task tutti `PASS`;
- diff limitato alla superficie prevista;
- test mirati e gate richiesti verdi;
- nessun segreto o dato operativo tracciato;
- documentazione tecnica aggiornata se cambia un contratto;
- `CODEX_STATE.md` e `NEXT_CODEX_TASKS.md` coerenti;
- commit e branch pubblicati senza force-push;
- gate umani lasciati agli esseri umani.
