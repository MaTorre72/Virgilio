# Next Codex Task

## CORRENTE - CONS-D03 - Runbook correnti brevi

Stato: `TODO`. Priorita`: `P1`.

Risultato: setup, sviluppo, test, operazioni e release hanno percorsi brevi,
non duplicati e basati su comandi verificati.

Dipendenze: `CONS-D02` chiuso `DONE`; architettura corrente canonica.

Componenti ammessi: documenti classificati `KEEP` o `MERGE` pertinenti ai
runbook, link, comandi ed evidenze del solo task.

Esclusioni: rimozione di file, modifica funzionale di codice o Apps Script,
servizi reali, build/deploy reali, modifica o merge di `main`.

Condizione di blocco: comando essenziale non verificabile offline o upstream
divergente.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-D03-AC1` setup e sviluppo hanno una sequenza minima univoca. | esecuzione comandi offline |
| `CONS-D03-AC2` test e smoke indicano ambito e ordine corretti. | prove mirate e smoke |
| `CONS-D03-AC3` operazioni distinguono uso utente e manutenzione. | confronto con architettura |
| `CONS-D03-AC4` release documenta build, verifica e vincoli senza deploy. | verifica comandi e link |
| `CONS-D03-AC5` fonti `MERGE`, diff, segreti e puntatori sono verificati. | controlli Git e documentali |

## SUCCESSIVO

`CONS-D04` - storia 1.1 condensata e documenti storici fuori dal percorso corrente.
