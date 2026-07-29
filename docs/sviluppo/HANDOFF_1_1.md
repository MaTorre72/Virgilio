# Handoff Virgilio 1.1.0

Questo documento registra la chiusura del programma `CONS`. La pull request
finale [#1](https://github.com/MaTorre72/Virgilio/pull/1) da
`codex/v1.1-development` e` stata revisionata e unita da un umano: `main`
contiene ora la release ufficiale 1.1.0 al merge commit `77730b3`.

## Consegna

- release ufficiale `1.1.0`, con versione unica e note pubbliche in
  `README.md` e `CHANGELOG.md`;
- build di collaudo originaria non pubblicata
  `CaronteSetup-1.1.0-68f3b90.exe`, SHA-256
  `8CD723E3DF14DFB30DE1E17D5BDDC29C81E3C87558DCBC85CA33828AE40DDE92`,
  Build ID `8268f442-8066-45c3-a9bc-0b32f6acdc76`; il binario e` perduto e
  nell'annotazione del tag ne restano soltanto identita` e metadati;
- [build di distribuzione pubblicata](https://github.com/MaTorre72/Virgilio/releases/tag/v1.1.0)
  `CaronteSetup-1.1.0-68f3b90-build-20260729.exe`, 30.704.281 byte, SHA-256
  `A6C87E6748ACC8C72970353B4686F219B28412D444847E7E436C818FB07DDB11`,
  Build ID `254daca5-af1d-4951-85dd-f1119a3f0437`, manifest
  `oauth_client_included=false`;
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
- rebuild pubblico dal tag immutato: build, smoke applicazione, installazione,
  avvio delle due GUI e disinstallazione `PASS`; tre asset riscaricati da
  GitHub con dimensioni e hash identici ai locali;
- onboarding ripetuto da clone pulito usando la sola dichiarazione del package.

## Rischi residui e gate umani

I limiti operativi restano quelli descritti in
[Operazioni e manutenzione](../tecnica/OPERAZIONI_E_MANUTENZIONE.md): in particolare la
sincronizzazione del Limbo dipende da Google Drive per desktop e puo` richiedere
retry limitati. L'installer pubblico e` privo di firma Authenticode e del client
OAuth Desktop: provenienza e SHA-256 vanno verificati, mentre il client Google
deve essere predisposto esternamente dall'amministratore. L'annotazione del tag
mantiene l'identita` storica del primo build; Release body e manifest
identificano senza ambiguita` l'asset scaricabile. Per una nuova release,
revisione e merge in `main` restano esclusivamente umani; il merge gia`
avvenuto non autorizza modifiche dirette future.
