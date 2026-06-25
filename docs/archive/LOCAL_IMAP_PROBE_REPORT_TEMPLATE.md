# Rapporto prova Local IMAP read-only

> Compilare senza password, token, corpi email, nomi degli allegati o dati personali.

## Configurazione controllata

| Campo | Valore |
|---|---|
| Data e ora della prova | DA COMPILARE |
| Operatore | DA COMPILARE |
| Provider testato | DA COMPILARE |
| Host IMAP | DA COMPILARE |
| Porta | 993 / DA COMPILARE |
| Metodo di autenticazione | Password applicazione / OAuth2 / altro: DA COMPILARE |
| Cartella/label osservata | `Virgilio/da-traghettare` / DA COMPILARE |
| Modalita' | dry-run / download locale controllato |

## Risultati

| Verifica | Risultato |
|---|---|
| Numero messaggi rilevati | DA COMPILARE |
| Numero allegati rilevati | DA COMPILARE |
| Allegati ammessi dalla policy | DA COMPILARE |
| Allegati rifiutati dalla policy | DA COMPILARE |
| I messaggi non diventano letti | CONFERMATO / NON CONFERMATO |
| I messaggi non vengono spostati | CONFERMATO / NON CONFERMATO |
| Nessun flag o contenuto IMAP modificato | CONFERMATO / NON CONFERMATO |

## Problemi osservati

- DA COMPILARE

## Decisioni aperte

- Mappatura provider tra label e cartella IMAP: DA DECIDERE.
- Metodo di autenticazione definitivo: DA DECIDERE.
- Limite massimo allegato: DA CONFERMARE.
- Retention e cancellazione della quarantena: DA DECIDERE.
- Scanner antivirus locale: NON IMPLEMENTATO.

## Esito della prova

- [ ] Superata: comportamento read-only verificato manualmente prima e dopo il probe.
- [ ] Non superata: interrompere il collaudo e conservare soltanto metadati tecnici minimi.
