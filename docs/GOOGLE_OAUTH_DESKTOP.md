# Client OAuth Desktop di Caronte

Questa procedura riguarda chi prepara la distribuzione. L'utente finale non
deve creare progetti, scegliere file o copiare codici e token.

## Registrazione una tantum

1. Nel progetto Google amministrato dal titolare di Caronte, configurare la
   schermata consenso con nome applicazione `Caronte`.
2. Creare un client OAuth di tipo **App desktop**.
3. Abilitare l'accesso necessario e dichiarare lo scope Gmail IMAP
   `https://mail.google.com/`.
4. Scaricare la configurazione del client e rinominarla
   `google_oauth_client.json`.
5. Conservare il file fuori dal repository. Il pattern e` escluso da Git.

Google considera le app installate incapaci di mantenere segreto il client;
questo file identifica Caronte, mentre i token dei singoli utenti restano
separati e protetti in Gestione credenziali Windows.

## Build predisposta

Passare il file soltanto durante la build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev\build_caronte.ps1 `
  -GoogleOAuthClientPath C:\percorso-protetto\google_oauth_client.json
```

La build valida che si tratti di un client Desktop e lo incorpora nella
cartella risorse della distribuzione. Caronte usa quindi il browser di sistema
e una callback locale su `127.0.0.1`; non mostra all'utente file tecnici.

## Pubblicazione Google

Per prove controllate, limitare il consenso agli utenti di test autorizzati.
Prima di distribuire Caronte a utenti esterni, completare gli adempimenti Google
richiesti per lo scope Gmail. Se l'applicazione resta interna a una
organizzazione Google Workspace, applicare la policy interna del dominio.
