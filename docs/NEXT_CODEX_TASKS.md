# Next Codex Task

## CORRENTE - CONS-G01 - Inventario superfici raggiungibili

Stato: `TODO`. Priorita`: `P1`.

Risultato: entry point, comandi, import pubblici e file inclusi nella build sono
mappati con la loro raggiungibilita` dai target supportati.

Dipendenze: `CONS-D04` chiuso `DONE`; percorso documentale corrente separato
dalla storia.

Componenti ammessi: configurazione package/build, entry point, parser CLI,
moduli importati dai target, test di packaging e inventario dedicato.

Esclusioni: rimozioni o refactor, modifica funzionale, servizi reali,
build/deploy reale, modifica o merge di `main`.

Condizione di blocco: entry point non classificabile senza esecuzione reale,
configurazione build divergente o upstream divergente.

| Criterio | Prova prevista |
| --- | --- |
| `CONS-G01-AC1` gli entry point installati e di sviluppo sono enumerati. | confronto metadata, script e help |
| `CONS-G01-AC2` ogni comando CLI e` associato al relativo dispatch. | ricerca parser e test help |
| `CONS-G01-AC3` gli import dei target supportati sono tracciati fino ai moduli diretti. | ricerca statica mirata |
| `CONS-G01-AC4` i file inclusi in wheel, eseguibili e installer sono inventariati. | configurazione build e test packaging |
| `CONS-G01-AC5` inventario, diff, segreti e puntatori sono verificati. | controlli Git e documentali |

## SUCCESSIVO

`CONS-G02` - GUI legacy `gui`/`gui_*` e test esclusivi rimossi senza impatto sui target.
