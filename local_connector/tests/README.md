# Test suite

La suite usa `pytest`/`unittest`, fixture sintetiche e tre livelli esclusivi.
L'inventario vincolante e` in `conftest.py`: ogni modulo `test_*.py` deve essere
classificato una sola volta, altrimenti la raccolta fallisce.

- `unit`: un singolo componente, dipendenze sostituite e nessun flusso esterno;
- `contract`: API, formati, superfici, packaging e compatibilita` osservabile;
- `integration_offline`: piu` componenti con fake, directory temporanee e dati
  sintetici; rete e servizi reali sono vietati.

Esecuzione separata e ripetibile dalla radice del repository:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\test_local_connector_level.ps1 -Level unit
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\test_local_connector_level.ps1 -Level contract
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\test_local_connector_level.ps1 -Level integration_offline
```

Lo smoke resta l'unico gate completo: raccoglie ed esegue tutti i livelli una
sola volta, poi verifica CLI, file di governance e assenza di segreti tracciati.

Copertura attuale:

- validazione e round-trip del contratto JSON;
- blocco di campi inattesi e payload operativi non confermati;
- sanitizzazione nomi e SHA-256;
- policy iniziale sulle estensioni;
- transizioni valide e non valide della quarantena;
- regola di ack dopo conferma del Limbo Drive;
- confinamento degli import di rete e adapter IMAP simulato;
- garanzia read-only: `SELECT readonly=True`, `BODY.PEEK[]`, nessun comando mutante.
- rilevazione di `conflict_cross_machine` senza risoluzione automatica; la procedura
  operativa manuale e' documentata in
  `docs/tecnica/OPERAZIONI_E_MANUTENZIONE.md`.

La suite automatica non usa mailbox, credenziali, Drive, Bucoliche o allegati reali.
