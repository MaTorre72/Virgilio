# Rapporto prova Local IMAP read-only - 2026-06-23

## Configurazione controllata

| Campo | Valore verificato |
|---|---|
| Data della prova | 2026-06-23 |
| Provider testato | Gmail personale, casella dedicata ai test |
| Host IMAP | `imap.gmail.com` |
| Porta | `993` |
| Sicurezza trasporto | IMAP4/SSL |
| Metodo di autenticazione | Verifica in due passaggi e password per l'app |
| Cartella/label osservata | `Virgilio/da-traghettare` |
| Modalita' eseguite | dry-run, poi download locale controllato |

Il rapporto non contiene indirizzo della casella, password, token, oggetti,
mittenti, nomi degli allegati o contenuto dei messaggi.

## Risultati

| Verifica | Risultato |
|---|---|
| Messaggi rilevati | 2 |
| Allegati rilevati | 2 |
| Allegati ammessi dalla policy | 2 |
| Allegati rifiutati dalla policy | 0 |
| Allegati salvati in quarantena | 2 |
| Stato SQLite degli allegati | `ready_for_scan`: 2 |
| Integrita' SQLite | `PRAGMA quick_check`: `ok` |
| Dry-run senza file o database | Confermato |
| Messaggi rimasti non letti dopo dry-run | Confermato manualmente |
| Messaggi rimasti non letti dopo download | Confermato manualmente |
| Etichetta rimasta invariata | Confermato manualmente |
| Messaggi non spostati | Confermato manualmente |
| Chiamate a Caronte o Drive | Nessuna |

## Comportamento IMAP verificato

- La cartella e' stata aperta con `SELECT readonly=True`.
- I messaggi sono stati acquisiti con `UID FETCH (BODY.PEEK[])`.
- Non sono stati eseguiti `STORE`, `COPY`, `MOVE`, `DELETE` o `EXPUNGE`.
- Non e' stato eseguito alcun ack.

## Problemi osservati

- Nessun problema funzionale osservato durante il probe.
- Il mapping della label Gmail nella cartella IMAP configurata ha funzionato per
  la casella di test impiegata; non e' ancora generalizzabile ad altri provider.

## Decisioni aperte

- Confermare il limite massimo allegato prima di un pilota piu' ampio.
- Definire retention e cancellazione verificabile della quarantena.
- Introdurre in una micro-fase separata la scansione antivirus locale.
- Confrontare MIME dichiarato, estensione e firma reale del contenuto.
- Mantenere esclusi ack IMAP, Caronte e Drive fino a nuove verifiche dedicate.

## Esito

**SUPERATA.** Il comportamento read-only e' stato verificato manualmente sia
dopo il dry-run sia dopo il download locale controllato.
