# Next Codex Task

## CORRENTE - CONS-C05 - Test organizzati per livello

Stato: `TODO`. Priorita`: `P1`.

Risultato: la suite distingue in modo ripetibile test di unita`, contratti,
integrazione offline e smoke, preservando copertura e comportamento.

Dipendenze: `CONS-C04` chiuso `DONE`; primo confine operativo estratto e
caratterizzato.

Componenti ammessi: configurazione e organizzazione dei test locali, marcatori,
script smoke e relativi puntatori.

Esclusioni: refactor applicativi, nuovi comportamenti, servizi reali, deploy,
modifica o merge di `main`.

Condizione di blocco: i livelli non sono separabili senza perdere test o
duplicare esecuzioni, oppure upstream diverge.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-C05-AC1` ogni livello ha confini e criteri espliciti. | inventario suite |
| `CONS-C05-AC2` unita` e contratti sono eseguibili separatamente. | comandi mirati |
| `CONS-C05-AC3` integrazione offline non usa servizi reali. | esecuzione isolata |
| `CONS-C05-AC4` lo smoke resta ingresso completo e ripetibile. | smoke locale |
| `CONS-C05-AC5` copertura, diff, segreti e puntatori sono verificati. | confronto raccolta e controlli Git |

## SUCCESSIVO

`CONS-H01` - guida di onboarding e prova da clone pulito ripetibile.

## EVIDENZA CONS-C04

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| --- | --- | --- | --- |
| `CONS-C04-AC1` | inventario circoscritto | `multi_account.py` primo operativo non GUI: 766 righe; parser YAML identificato come responsabilita` sintattica autonoma | `PASS` |
| `CONS-C04-AC2` | ispezione import e struttura | `local_config_yaml.py` non importa moduli operativi; dipendenza unidirezionale da `multi_account` | `PASS` |
| `CONS-C04-AC3` | test di caratterizzazione | errori pubblici e messaggi caratterizzati; test area `80 passed` | `PASS` |
| `CONS-C04-AC4` | test mirati offline | configurazione, multi-account e migrazioni locali `80 passed` senza servizi reali | `PASS` |
| `CONS-C04-AC5` | test a scalare e controlli Git | smoke locale `546 passed`; diff, segreti e puntatori verificati | `PASS` |
