# Next Codex Task

## CORRENTE - CONS-C04 - Primo modulo operativo separato per responsabilita`

Stato: `TODO`. Priorita`: `P1`.

Risultato: il primo modulo operativo monolitico selezionato tramite evidenza e`
separato in responsabilita` coese, preservandone integralmente il comportamento
osservabile.

Dipendenze: `CONS-C03` chiuso `DONE`; bootstrap, parser e dispatch CLI separati.

Componenti ammessi: un solo modulo operativo monolitico scelto con metriche,
suoi test di caratterizzazione e relativi puntatori.

Esclusioni: secondo modulo operativo, cambi di semantica, GUI, servizi reali,
deploy, modifica o merge di `main`.

Condizione di blocco: nessun confine coeso e behavior-preserving e` dimostrabile
con test di caratterizzazione oppure upstream diverge.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-C04-AC1` il modulo target e` scelto con metriche e responsabilita` esplicite. | inventario circoscritto |
| `CONS-C04-AC2` i confini estratti sono coesi e senza dipendenze cicliche. | ispezione import e struttura |
| `CONS-C04-AC3` il comportamento pubblico resta invariato. | test di caratterizzazione |
| `CONS-C04-AC4` errori ed effetti locali restano invariati. | test mirati offline |
| `CONS-C04-AC5` suite richiesta, diff, segreti e puntatori sono verificati. | test a scalare e controlli Git |

## SUCCESSIVO

`CONS-C05` - test organizzati per unita`, contratti, integrazione offline e smoke.
