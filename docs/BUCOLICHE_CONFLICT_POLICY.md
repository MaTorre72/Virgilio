# Policy manuale conflitti Bucoliche

Questa policy si applica quando `Bucoliche_Stato` espone `conflict_type=conflict_cross_machine`.
Il caso indica che lo stesso `fingerprint` e' arrivato da piu' `machine_id` con esiti terminali
incompatibili. Virgilio non risolve mai questo caso in automatico: SQLite locale resta la fonte
operativa primaria e Bucoliche resta una vista condivisa per audit.

## Segnale di conflitto

Trattare una riga come conflitto manuale quando sono presenti tutti questi elementi:

- `current_global_state=conflict`
- `conflict_type=conflict_cross_machine`
- `notes` JSON con `cross_machine_conflict=true`
- `notes.machine_states` valorizzato con almeno due macchine

## Procedura operativa

1. Fermare qualunque azione manuale irreversibile su quel `fingerprint` finche' il caso non e' chiarito.
2. Aprire il `state.db` locale di ciascuna macchina indicata in `notes.machine_states`.
3. Ricostruire per ogni macchina la sequenza minima: allegato, `result`, `global_state_suggestion`,
   timestamp evento e file in staging associato.
4. Identificare la macchina sorgente affidabile in base a stato locale, presenza del file e ultimo evento coerente.
5. Scegliere una sola decisione operativa finale:
   `completed` se l'allegato giusto e' gia' stato gestito correttamente;
   `failed` se l'input e' da rigettare;
   `duplicate_seen` se una macchina ha solo visto un duplicato gia' trattato altrove;
   `skipped` se l'allegato non va processato per una regola nota.
6. Correggere solo la macchina non autorevole: evitare export ripetuti, rimuovere o isolare il file locale errato,
   e lasciare traccia dell'azione in note operative o ticket esterno.
7. Rieseguire in `--dry-run` il flusso locale sulla macchina corretta e verificare che l'evento successivo
   non produca un nuovo conflitto.
8. Rieseguire l'export Bucoliche dalla macchina autorevole e controllare che `Bucoliche_Stato` torni coerente.

## Cosa non fare

- Non modificare a mano `Bucoliche_Eventi` o `Bucoliche_Stato`.
- Non usare Bucoliche come fonte unica per decidere il risultato finale.
- Non lanciare ack, Gmail o Google reali solo per chiudere il conflitto.
- Non tentare merge automatici tra record di macchine diverse.

## Evidenze minime da conservare

- `fingerprint` coinvolto
- `machine_id` coinvolti
- stato finale deciso e motivo
- timestamp dell'ultima verifica
- riferimento al log o ticket locale usato per la correzione
