# Trasporto pilota tramite Google Drive Desktop

## Scopo

Questa micro-fase valuta Google Drive Desktop come trasporto file economico e
reversibile. Il Local IMAP Connector copia gli allegati gia' in stato
`ready_for_caronte` in una cartella locale scelta dall'operatore e sincronizzata
da Drive Desktop. Accanto a ogni file viene scritto un manifest JSON metadata-only.

Non viene usata Drive API e Caronte non riceve byte, base64 o percorsi locali.

## Perche' Drive Desktop per il pilota

- riusa un client di sincronizzazione gia' disponibile sul PC;
- evita per ora OAuth, upload resumable e gestione quote Drive API;
- mantiene osservabili file e manifest nel filesystem locale;
- consente di interrompere il pilota disabilitando una variabile d'ambiente;
- non modifica il file sorgente conservato in quarantena.

## Quarantena e staging sono perimetri diversi

| Perimetro | Funzione | Sincronizzazione |
|---|---|---|
| `.local_data/quarantine/ready` | Copia locale controllata e scansionata | Deve restare non sincronizzata |
| `VIRGILIO_LOCAL_DRIVE_STAGING_DIR` | Limbo locale di trasporto pilota | Gestita esternamente da Drive Desktop |

Lo staging non e' una cartella pratica e non e' archiviazione definitiva. Lo stato
`staged_local_drive` significa soltanto che copia e manifest sono presenti nella
directory locale configurata; non dimostra che Google li abbia sincronizzati.

## Dipendenze e configurazione

- Google Drive Desktop installato e configurato dall'utente;
- cartella Limbo di test gia' esistente dentro il filesystem Drive Desktop;
- directory scrivibile dal processo del connettore;
- `VIRGILIO_LOCAL_DRIVE_STAGING_ENABLED=true`;
- `VIRGILIO_LOCAL_DRIVE_STAGING_DIR` con percorso assoluto locale.

Il connettore non crea la directory configurata e non cerca automaticamente il
mount di Drive Desktop.

## Semantica della copia

1. selezione dei soli record `ready_for_caronte` dell'ultimo run completato;
2. copia in un file esclusivo con suffisso `.uploading`;
3. flush e `fsync`;
4. ricalcolo SHA-256 sulla copia;
5. rename al nome finale univoco;
6. scrittura atomica del manifest tramite `.partial`;
7. aggiornamento SQLite a `staged_local_drive`.

Un errore dopo l'avvio produce `staging_failed`. Il connettore non cancella file
dalla directory di staging e non cancella mai l'originale in quarantena.

## Manifest

Il manifest contiene identificativi locali, nomi, hash, dimensione, MIME dichiarato,
esito scanner, riferimenti messaggio, alias account e timestamp. La nota fissa e':

`File copiato in cartella locale sincronizzata; sync cloud non verificata.`

Il manifest non contiene password, token, byte, base64 o percorsi locali assoluti.

## Limiti e rischi

- nessuna conferma di sincronizzazione cloud;
- conflitti, pause, quota e stato Drive Desktop non sono osservati;
- file e manifest possono arrivare nel cloud in momenti diversi;
- un processo esterno puo' rinominare o rimuovere file;
- il rename atomico vale nel filesystem locale, non nella sincronizzazione cloud;
- nessuna autenticazione o correlazione server-side con Caronte;
- retention e pulizia dello staging non sono implementate.

## Confronto sintetico

| Opzione | Vantaggi | Svantaggi in questa fase |
|---|---|---|
| Drive Desktop | Economico, semplice, reversibile, nessun OAuth nel connector | Nessuna conferma cloud o idempotenza remota |
| Drive API | Upload verificabile, ID file, controllo errori | OAuth, quote, retry e sicurezza piu' complessi |
| Base64 Apps Script | Un solo endpoint JSON | Overhead, limiti payload e rischio memoria; escluso |
| rclone | Maturo, supporta checksum e molti backend | Dipendenza/configurazione operativa aggiuntiva; non attivato |

## Perche' non e' archiviazione definitiva

Il Limbo di test non assegna il documento a cliente, sito o pratica; non produce
ID Drive verificato, non scrive Bucoliche e non applica retention. L'eventuale
sincronizzazione e' un trasporto intermedio, non una presa in carico documentale.

## Prossima decisione

Dopo un test manuale va deciso come verificare in modo read-only la comparsa cloud
di file e manifest. Solo dopo tale verifica si potra' progettare la presa in carico
da parte di Caronte, ancora senza ack Gmail automatico.
