# Sicurezza e strategia di test

## Obiettivo

Virgilio tratta documenti provenienti da email e coordina piu` sistemi. La
sicurezza della 1.1 dipende da quattro proprieta`: fermarsi in sicurezza,
riconoscere i retry, non esporre segreti e non dichiarare un completamento prima
che tutte le post-condizioni siano vere.

## Modello di minaccia essenziale

| Rischio | Esempio | Controllo della 1.1 |
| --- | --- | --- |
| allegato ostile | eseguibile, macro o archivio camuffato | allowlist, quarantena, scanner e nessuna apertura automatica |
| traversal | nome file con `..` o percorso assoluto | sanitizzazione e percorsi relativi sotto una radice verificata |
| duplicazione | retry dopo timeout Drive | identita` stabili, hash, manifest e vincoli SQLite |
| file sbagliato | collisione di nome nel Limbo | niente overwrite silenzioso, hash e conflitto esplicito |
| falsa conclusione | ack prima dell'archiviazione | macchina a stati e post-condizione su tutti gli allegati |
| fuga di credenziali | password in YAML o log | variabili ambiente/deposito Windows, redazione e ignore Git |
| confusione account | errore di una casella attribuito a un'altra | `account_alias` obbligatorio e isolamento per account |
| payload remoto eccessivo | byte o path locale inviati a GAS | intake metadata-only e ID Drive opachi |
| modifica involontaria mail | lettura che imposta `Seen` | IMAP read-only e `BODY.PEEK` |
| deploy involontario | test che pubblica Apps Script | `clasp push` e deploy fuori dagli smoke |

## Policy allegati

- dimensione massima configurabile, con default d'esempio 25 MiB;
- estensioni ammesse tramite policy esplicita;
- documenti Office (`.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`) ammessi
  soltanto con scansione obbligatoria;
- formati macro-enabled, archivi compressi, script ed eseguibili bloccati;
- hash SHA-256 calcolato sui byte acquisiti;
- file mai aperto automaticamente dal connettore;
- scanner `auto` seleziona il motore locale disponibile e fallisce in modo
  conservativo quando il gate richiesto non e` affidabile.

`scan_failed` non equivale a pulito. Un file non verificato resta fuori dal
Limbo finche` la policy non consente esplicitamente un percorso sicuro.

## Segreti e dati locali

Non vengono versionati:

- `.env` e varianti;
- `accounts.local.yaml` e configurazioni operative;
- `.local_data/`, `.secrets/` e `_staging/`;
- `.clasprc.json`, token OAuth e JSON di service account;
- password, app password, webhook e ID reali quando sensibili.

Gli esempi usano domini `.invalid`, alias neutri e valori vuoti. Un test non
deve leggere il deposito credenziali reale ne` ereditare variabili operative
senza sostituirle con valori sintetici.

## Confini di rete

La suite automatica e` offline. IMAP, Google, Drive, Chat e Telegram sono
sostituiti con fake o fixture. Un test che richiede rete reale non appartiene
allo smoke repository.

L'integrazione tra connettore e Apps Script scambia metadati. Sono vietati:

- byte dell'allegato;
- stringhe base64 del contenuto;
- percorsi assoluti o relativi del PC;
- credenziali o token;
- errori grezzi che possano esporre dati sensibili.

## Livelli di test

| Livello | Scopo | Dipendenze consentite |
| --- | --- | --- |
| `unit` | singola regola o servizio isolato | memoria, `tmp_path`, fake |
| `contract` | formati pubblici e confini tra componenti | payload sintetici e file locali |
| `integration_offline` | flusso tra piu` componenti | SQLite temporaneo, filesystem temporaneo, fake di rete |
| smoke repository | regressione complessiva locale | i tre livelli precedenti, controlli governance e segreti |
| smoke build | avvio e contenuto dell'eseguibile | artefatto locale costruito |
| smoke installer | installazione/disinstallazione controllata | ambiente Windows dedicato |
| gate umano | comportamento operativo reale autorizzato | dati non critici e rollback documentato |

La suite finale della baseline 1.1 contiene 548 test offline. Questo numero e`
un'evidenza della release, non un vincolo fisso: una modifica puo` aumentarlo,
ma non deve ridurre la copertura dei contratti per adattare un test al codice.

## Sequenza di verifica per una modifica

1. aggiungere o aggiornare il test mirato che dimostra il criterio;
2. eseguire il file o il livello interessato;
3. eseguire i test dell'area attraversata;
4. quando si toccano percorso locale o governance, eseguire lo smoke completo;
5. se si cambia packaging, eseguire smoke build e installer pertinenti;
6. verificare diff, tree e assenza di segreti prima del commit.

Comandi e parametri sono nel [Riferimento comandi](RIFERIMENTO_COMANDI.md).

## Casi di regressione da proteggere

- una fetch IMAP non imposta `Seen`;
- l'errore su un account non ferma gli altri;
- lo stesso UID non produce una seconda mail nello stesso account;
- due contenuti con nome uguale ma hash diverso generano conflitto;
- un allegato rifiutato non raggiunge il Limbo;
- la mancata visibilita` Drive resta in attesa senza duplicare;
- Apps Script rifiuta path locali e payload non conformi;
- Da archiviare non crea una seconda riga attiva equivalente;
- una mail multi-allegato non riceve ack finche` manca un documento;
- l'ack non usa delete, move o expunge e verifica le etichette finali;
- backup e reset rispettano lock, radice e integrita`;
- la GUI utente non mostra token, path, fingerprint o traceback.

## Gate umani

Codex e gli smoke non possono approvare autonomamente:

- connessione a caselle o Google reali;
- modifica di etichette reali;
- `clasp push` o deployment;
- reset di dati operativi;
- installazione di una release in produzione;
- conferma che il flusso soddisfi il lavoro degli utenti.

Il collaudo umano della baseline e` `PASS` del 28 luglio 2026. Nuove modifiche
che alterano un comportamento operativo richiedono un nuovo gate proporzionato,
non ereditano automaticamente quel PASS.

## Controlli prima della distribuzione

- versione package, manifest build e nome installer coincidono;
- commit e Build ID sono tracciabili;
- SHA-256 dell'installer coincide con quello pubblicato;
- nessun file operativo o segreto e` incluso nell'artefatto;
- le icone provengono esclusivamente da `icone/`;
- il deployment Apps Script previsto e` identificato senza eseguire push
  impliciti;
- backup e rollback sono disponibili prima di ogni prova reale.

Le procedure sono descritte in
[Operazioni e manutenzione](OPERAZIONI_E_MANUTENZIONE.md).
