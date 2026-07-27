# Next Codex Tasks

## CORRENTE - WAITING_HUMAN_REVIEW

`GUI-U-R05-T07` e` `DONE`: la strategia esplicita `move_to_done_label`
applica `traghettate` e rimuove soltanto l'etichetta di ingresso, senza
cancellazione o expunge. Test mirati `73 passed`; smoke locale `581 passed`.

## CODA

Nessun task automatico.

Il correttivo Registro unico e Limbo piatto e` pubblicato sul deployment esistente come versione `35`.
La RC desktop `CaronteSetup-0.11.0-2294efa.exe` e` installata, il collegamento
protetto e` configurato e il reset TEST `reset-r05-20260726-2139` e` completato
con backup. Registro, Inbox e Limbo piatto sono vuoti; il foglio contiene soltanto
`bucoliche` e `Virgilio_Inbox`. Il trigger TEST resta fermo.

Successore unico: produrre/installare la nuova RC dal commit atomico di T07,
impostare la strategia nella configurazione installata e collaudare su Gmail TEST.
Le quattro mail gia` completate richiedono una sola rimozione dell'etichetta
`da-traghettare`; nessuna ulteriore modifica automatica.
