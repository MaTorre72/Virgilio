# Next Codex Tasks

## CORRENTE - DONE

`GUI-U-R05-T11` corregge il caso MIME annidato osservato il 2026-07-28,
deduplica la stessa identita` IMAP tra scanner/processor e cicli successivi e
segnala esplicitamente le mail trovate senza allegati acquisibili. Prove solo
sintetiche: mirati `132 passed`, suite e smoke `599 passed`. Nessuna operazione
su Gmail, Google o dati reali.

## SUCCESSIVO - WAITING_HUMAN_REVIEW

La RC `0.11.0-7e18277` contenente T11 e` stata generata, verificata e installata.
Ripetere il collaudo umano focalizzato sulla mail MIME reale e verificare l'intero
percorso fino a `traghettate`.

## GATE - WAITING_HUMAN_REVIEW

`GUI-U-R05-T10` e `GUI-U-R05-T11` sono `DONE`. La RC installata
`0.11.0-7e18277` include completamento Gmail, parser MIME annidato,
deduplicazione dei messaggi e reporting esplicito. Apps Script resta al
deployment `40`.

## CODA

Successore unico: eseguire il collaudo umano dalla mail MIME reale fino al
passaggio finale `da-traghettare` -> `traghettate`. Codex non compila o approva
l'esito.
