# Next Codex Tasks

## CORRENTE - DONE

`GUI-U-R05-T11` corregge il caso MIME annidato osservato il 2026-07-28,
deduplica la stessa identita` IMAP tra scanner/processor e cicli successivi e
segnala esplicitamente le mail trovate senza allegati acquisibili. Prove solo
sintetiche: mirati `132 passed`, suite e smoke `599 passed`. Nessuna operazione
su Gmail, Google o dati reali.

## SUCCESSIVO

Generare e installare una nuova RC contenente T11 solo su richiesta esplicita;
poi ripetere il collaudo umano focalizzato sulla mail MIME reale. La RC corrente
`0.11.0-e9e0949` non contiene T11.

## GATE - WAITING_HUMAN_REVIEW

`GUI-U-R05-T10` e` `DONE`: follow-up persistente senza nuova acquisizione e
rimozione sicura dell'etichetta Gmail dalla cartella destinazione sono coperti
da suite e smoke `595 passed`. Il caso reale ha completato quattro mail e la
coda `da-traghettare` e` vuota. La RC `0.11.0-e9e0949` e` stata generata,
verificata e installata; Apps Script resta al deployment `40`.

## CODA

Successore unico: eseguire il collaudo umano focalizzato sul passaggio finale
`da-traghettare` -> `traghettate`. Codex non compila o approva l'esito.
