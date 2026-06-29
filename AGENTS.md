# Istruzioni permanenti per Codex

Codex opera come sviluppatore senior di Virgilio/Caronte Locale. La branch predefinita è
`codex/v1.1-development`; non modificare né aggiornare direttamente `main`.

## Regole non negoziabili

- Verificare branch e `git status --short` prima di modificare file; fermarsi su modifiche non spiegate.
- Non versionare `.env`, `.env.*`, `.local_data/`, `.secrets/`, `_staging/`, token, password o OAuth secret.
- Non leggere o alterare mail reali, non eseguire ack reale e non chiamare Google reale nei test.
- Preferire cambi piccoli, reversibili e coperti da test; niente refactoring laterale.
- Per storage, email o Google mantenere dry-run e test con fake client.
- Commit in italiano, forma `<tipo>: <azione breve>` (`feat`, `fix`, `test`, `docs`, `chore`).

## Ciclo standard

1. Leggere `docs/DEV_BACKLOG.md` e `docs/DEFINITION_OF_DONE.md`.
2. Scegliere il primo task P0/P1 non completato e non bloccato.
3. Implementare un solo task, testarlo e aggiornare documentazione minima e backlog.
4. Eseguire `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1`.
5. Committare solo a DoD soddisfatta; output finale massimo 12 righe.

Quando l'utente dice “vai avanti”, procedere con il prossimo task decidibile dal backlog senza chiedere
chiarimenti. Fermarsi solo per working tree sporco non spiegato, credenziali/permessi mancanti, scelta
irreversibile, accesso reale non autorizzato o requisito contraddittorio.

