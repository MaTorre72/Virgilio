# Next Codex Tasks

## CORRENTE - GUI-U-R05-T02

Risultato: il reset locale esistente viene composto con stop runner, lock, backup verificato e
successiva nuova acquisizione.

Riuso obbligatorio:

- servizi runner/startup gia` esistenti;
- `reset_local_state`, backup e lock canonici;
- `MaintenanceService` e CLI condivisa;
- fixture filesystem, credenziali sintetiche e fake IMAP/storage esistenti.

Criteri binari:

1. Nessun reset parte con un runner attivo.
2. Il backup precede ogni modifica ed e` verificato.
3. Configurazione e credenziali restano; DB e quarantena sono ricreati.
4. L'esito espone conservato, azzerato e percorso backup.
5. Il primo ciclo successivo riacquisisce e copia con fake IMAP/storage.

Esclusioni: GAS, rete reale, reset remoto, retention, build/installer, modifiche estetiche. Blocco:
impossibile garantire esclusione reciproca tra worker e reset.

## CODA

1. `GUI-U-R05-T03` - azzeramento coerente e recuperabile dell'ambiente TEST locale/Registro/Limbo.
2. `GUI-U-R05-T04` - soppressione eventi invariati, RC identificata e collaudo finale.

Una run non anticipa task in coda.
