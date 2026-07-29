# Handoff Virgilio 1.1.0

Questo documento registra la chiusura del programma `CONS`. La pull request
finale [#1](https://github.com/MaTorre72/Virgilio/pull/1) da
`codex/v1.1-development` e` stata revisionata e unita da un umano: `main`
contiene ora la release ufficiale 1.1.0 al merge commit `77730b3`.

## Consegna

- release ufficiale `1.1.0`, con versione unica e note pubbliche in
  `README.md` e `CHANGELOG.md`;
- installer `CaronteSetup-1.1.0-68f3b90.exe`, SHA-256
  `8CD723E3DF14DFB30DE1E17D5BDDC29C81E3C87558DCBC85CA33828AE40DDE92` e
  Build ID `8268f442-8066-45c3-a9bc-0b32f6acdc76`;
- tag annotato remoto `v1.1.0`, oggetto `096f195`, sul commit sorgente release
  `68f3b90`;
- documentazione, superfici supportate, repository, API package, CLI,
  configurazione e livelli di test consolidati dal programma `CONS`;
- documentazione corrente organizzata sotto `docs/utente`, `docs/tecnica` e
  `docs/sviluppo`, con la storia precedente recuperabile da Git.

## Prove finali

- baseline preservata: commit `7e18277`, `PASS` umano 2026-07-28 e Apps Script
  deployment `40`;
- audit finale: 208 file tracciati, 44/44 documenti inventariati prima di
  questo handoff, nessuna superficie legacy vietata o segreto operativo
  versionato;
- suite offline completa: `548 passed`;
- build Caronte e installer 1.1.0 completata; smoke build e installer `OK`;
- onboarding ripetuto da clone pulito usando la sola dichiarazione del package.

## Rischi residui e gate umani

I limiti operativi restano quelli descritti in
[Operazioni e manutenzione](../tecnica/OPERAZIONI_E_MANUTENZIONE.md): in particolare la
sincronizzazione del Limbo dipende da Google Drive per desktop e puo` richiedere
retry limitati. Per una nuova release, revisione e merge in `main` restano
esclusivamente umani; il merge gia` avvenuto non autorizza modifiche dirette
future.
