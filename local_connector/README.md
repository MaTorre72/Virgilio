# Virgilio Local Connector

Scaffolding del possibile connettore IMAP locale di Virgilio.

## Stato

**Solo piano e struttura. Nessuna connessione IMAP e' implementata.**

Questo progetto Python e' separato dagli script Google Apps Script presenti nella radice del repository. Il suo scopo futuro e' acquisire allegati da una cartella IMAP convenzionale, conservarli temporaneamente in quarantena locale e produrre un comando standardizzato per Caronte.

## Confini

Il connettore locale potra' occuparsi soltanto di:

- lettura IMAP limitata alla cartella configurata;
- download degli allegati selezionati dall'utente;
- quarantena e filtri locali;
- adapter per eventuale antivirus locale;
- costruzione del comando verso Caronte;
- ack della mail dopo conferma valida.

Restano in Apps Script:

- Drive e Limbo Drive;
- Bucoliche;
- notifiche;
- apertura e gestione delle pratiche;
- nucleo operativo Caronte.

## Struttura

```text
local_connector/
  README.md
  pyproject.toml
  src/
    virgilio_connector/
      __init__.py
  tests/
    README.md
```

I moduli applicativi verranno introdotti una micro-fase alla volta, soltanto dopo l'approvazione delle decisioni aperte.

## Documentazione

- [`../docs/LOCAL_IMAP_CONNECTOR.md`](../docs/LOCAL_IMAP_CONNECTOR.md)
- [`../docs/CONTRATTO_DATI_CARONTE.md`](../docs/CONTRATTO_DATI_CARONTE.md)
- [`../docs/QUARANTENA_LOCALE.md`](../docs/QUARANTENA_LOCALE.md)

## Credenziali

Non creare file di credenziali nel repository. La strategia futura per password applicative, OAuth2 o keyring locale e' **DA DECIDERE**.

I pattern principali per `.env`, token e credenziali sono gia' esclusi dal `.gitignore` della radice, ma l'assenza dal versionamento non sostituisce una gestione sicura dei segreti.

## Prossima micro-fase proposta

Implementare solo modelli dati e validazione locale, senza rete:

1. modelli richiesta/risposta coerenti con il contratto JSON;
2. sanitizzazione dei nomi file;
3. calcolo SHA-256 su file fittizi;
4. macchina a stati della quarantena;
5. test automatici deterministici.

La connessione IMAP reale resta esclusa dalla prossima micro-fase.
