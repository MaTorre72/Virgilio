# Next Codex Tasks

## CORRENTE - GUI-U-R05-T01

Risultato: se SQLite conosce un allegato ma il file locale e` assente, il processor esistente lo
riacquisisce; ogni `staging_failed`/`staging_conflict` blocca e descrive la pipeline.

Riuso obbligatorio:

- `MultiAccountImapProcessor` e `ReadonlyStateStore`;
- `LocalFilesystemStorageAdapter` e stati storage gia` definiti;
- `LocalPipelineRunner`, `ActivityService` e progressi Home esistenti;
- fixture/fake in `test_multi_account.py`, `test_pipeline.py`, `test_storage_adapter.py` e test Home.

Criteri binari:

1. Un record duplicato e` riusato solo se file locale e SHA-256 sono validi.
2. File assente o non valido provoca riacquisizione sicura, senza nuova pipeline parallela.
3. Lo storage persiste un evento azionabile per `staging_failed` e `staging_conflict`.
4. La pipeline termina `completed_with_errors` e non completa/consegna il messaggio coinvolto.
5. Test verticale fake: file mancante -> riacquisizione -> copia -> handoff; test mirati e smoke verdi.

Esclusioni: GAS, rete reale, reset, retention, build/installer, modifiche estetiche. Blocco: il recupero
richiederebbe mutazioni IMAP o un nuovo protocollo invece del download read-only gia` esistente.

## CODA

1. `GUI-U-R05-T02` - ripristino locale coordinato riusando reset, backup e runner esistenti.
2. `GUI-U-R05-T03` - azzeramento coerente e recuperabile dell'ambiente TEST locale/Registro/Limbo.
3. `GUI-U-R05-T04` - soppressione eventi invariati, RC identificata e collaudo finale.

Una run non anticipa task in coda.
