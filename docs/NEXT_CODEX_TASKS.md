# Next Codex Tasks

## CORRENTE - WAITING_HUMAN_REVIEW

`GUI-U-R05-T08` e` `DONE` nel repository: il completamento attende lo stato
finale `archiviato` di tutti gli allegati, verifica entrambe le etichette Gmail e
preserva/ripristina le tre anagrafiche canoniche. Test mirati `107 passed`;
regressione e smoke locale `587 passed`.

## CODA

Nessun task automatico.

Il deployment live resta alla versione `35` e la RC installata resta quella del
commit `fcc5c0c`: nessuno dei due contiene T08. Il reset TEST del 2026-07-27 ha
preceduto il collaudo che ha riprodotto i tre difetti; non rappresenta quindi lo
stato vuoto iniziale per un nuovo collaudo. Il trigger TEST resta fermo.

Successore unico, solo su richiesta esplicita: pubblicare il delta GAS sul
deployment esistente, produrre/installare la RC dal commit atomico di T08,
ripristinare `Clienti_Siti`, `Team` e `TipiPratica` da un backup verificato e poi
eseguire reset TEST e collaudo umano dall'inizio. Nessuna azione live automatica.
