# Rapporto E2E Caronte dry-run metadata-only - 2026-06-23

## Identificazione

| Campo | Valore |
|---|---|
| Data | 2026-06-23 |
| Branch | `connector/caronte-dry-run-bridge` |
| Commit bridge | `92e83b6` |
| Commit CLI usato | `29fde29` |
| Deployment Apps Script | Versione 11 |
| URL Web App | `https://script.google.com/macros/s/AKfy...W-CQ/exec` (oscurato) |

## Descrizione del test

Il progetto Apps Script Virgilio e' stato aggiornato con `caronte_bridge.gs` e con
il routing metadata-only in `doPost`. Il test puro `testCaronteBridgeDryRun` e'
stato eseguito nell'editor Apps Script con esito `OK` prima del deployment.

E' stato poi inviato un solo comando JSON dry-run gia' generato dal Local IMAP
Connector. Il client ha eseguito un unico POST, senza retry, file, multipart,
base64, byte o percorsi locali. L'URL reale e' conservato soltanto nel `.env`
locale escluso da Git.

## Comando eseguito

```powershell
python -m virgilio_connector send-caronte-dry-run `
  --command-file ".local_data\commands\dry-run\6256647b-285a-45c9-ba64-4ef589374f70.json"
```

## Payload sintetico rappresentativo

Il payload seguente descrive la forma inviata senza riportare oggetto, mittente,
Message-ID, hash o altri metadati del messaggio reale:

```json
{
  "action": "local_imap_dry_run",
  "payload": {
    "schema_version": "1.0",
    "connector_type": "local_imap",
    "requested_action": "stage_attachments_in_limbo",
    "dry_run": true,
    "user_confirmed_command": false,
    "attachments": [
      {
        "local_temp_id": "att-opaque-test",
        "sha256": "[64 caratteri esadecimali oscurati]",
        "quarantine_status": "ready_for_caronte",
        "scan_engine": "windows_defender",
        "scan_result": "clean"
      }
    ]
  }
}
```

## Risposta ricevuta

```json
{
  "ok": true,
  "dry_run": true,
  "accepted_attachments": 1,
  "rejected_attachments": 0,
  "limbo_drive_ids": [],
  "bucoliche_rows": [],
  "message": "Comando dry-run validato; nessun effetto operativo.",
  "errors": []
}
```

Verifiche automatiche sulla risposta:

- `ok = true`;
- `dry_run = true`;
- conteggi allegati coerenti con il comando;
- `limbo_drive_ids = []`;
- `bucoliche_rows = []`;
- nessun errore;
- nessun identificativo persistente restituito.

## Assenza di trasporto file ed effetti operativi

- Nessun file o byte allegato e' stato inviato.
- Nessun campo `local_path`, `file_path`, `file_bytes`, `base64`, `content` o `raw`
  e' stato ammesso nell'envelope.
- Nessun upload Drive o Limbo Drive e' stato richiesto.
- Nessuna scrittura Bucoliche, notifica o operazione Gmail e' presente nel ramo
  `caronteRiceviComandoDryRun`.
- Il client non ha modificato SQLite.

## Controlli manuali per Marco

- [ ] Drive: confermare che nel Limbo non siano comparsi nuovi file.
- [ ] Bucoliche: confermare che non siano comparse nuove righe.
- [ ] Gmail: confermare che i messaggi siano ancora non letti, etichettati e non
  spostati.
- [ ] Notifiche: confermare che non siano arrivati messaggi Chat o Telegram.

## Esito

**TEST DI RETE METADATA-ONLY SUPERATO.** Il bridge ha ricevuto e validato il
comando dry-run e ha restituito la risposta standard senza identificativi Drive o
Bucoliche. La chiusura operativa richiede ancora la checklist manuale sopra.

## Rischi residui

- Il deployment e' accessibile a `Chiunque`; il bridge non deve essere considerato
  autenticato. Valutare restrizione o autenticazione prima di ampliare l'uso.
- Non sono ancora definiti idempotenza server-side e audit persistente delle
  richieste dry-run.
- Il test copre un solo comando e un solo allegato metadata.
- Nessuna conclusione sul futuro trasporto file deriva da questo test.

## Prossima micro-fase consigliata

Chiudere la checklist manuale e produrre una decisione architetturale sul trasporto
file separato dai metadati, confrontando almeno upload autenticato diretto,
multipart controllato e URL firmati temporanei. Non implementare il trasporto fino
all'approvazione esplicita della decisione.
