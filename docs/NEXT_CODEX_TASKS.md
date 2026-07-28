# Next Codex Tasks

## CORRENTE - DONE

`GUI-U-R05-T11` corregge il caso MIME annidato osservato il 2026-07-28,
deduplica la stessa identita` IMAP tra scanner/processor e cicli successivi e
segnala esplicitamente le mail trovate senza allegati acquisibili. Prove solo
sintetiche: mirati `132 passed`, suite e smoke `599 passed`. Nessuna operazione
su Gmail, Google o dati reali.

## SUCCESSIVO - NESSUNO

La RC `0.11.0-7e18277` contenente T11 e` stata generata, verificata e installata.
Il collaudatore ha dichiarato `PASS` sul collaudo finale il 2026-07-28.

## GATE - PASS

`GUI-U-R05-T10` e `GUI-U-R05-T11` sono `DONE`. La RC installata
`0.11.0-7e18277` include completamento Gmail, parser MIME annidato,
deduplicazione dei messaggi e reporting esplicito. Apps Script resta al
deployment `40`.

`GUI-U-R05` e `GATE U-H3` sono chiusi dal `PASS` umano esplicito. Nessun task
operativo residuo e nessuna azione autonoma in coda.

## CODA

Nessuno. Eventuali evoluzioni richiedono un nuovo task esplicito.
