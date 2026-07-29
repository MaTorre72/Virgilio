# Documentazione tecnica

Questa sezione descrive la release ufficiale Virgilio 1.1.0 per chi deve
installarla, amministrarla o modificarla. La baseline funzionale e` il commit
collaudato `7e18277`, con collaudo umano `PASS` del 28 luglio 2026 e deployment
Apps Script `40`.

## Percorso consigliato per un nuovo sviluppatore

1. [Architettura](ARCHITETTURA.md): perche` esistono Virgilio, Caronte Locale e
   l'adapter Apps Script e dove passa ogni dato.
2. [Modello dati e stati](MODELLO_DATI_E_STATI.md): identita`, persistenza,
   idempotenza e condizioni di completamento.
3. [Installazione e comandi](INSTALLAZIONE_E_COMANDI.md): ambiente ripetibile e
   primo smoke offline.
4. [Configurazione e integrazioni](CONFIGURAZIONE_E_INTEGRAZIONI.md): confini
   con IMAP, Drive Desktop, Google e notifier.
5. [Sicurezza e test](SICUREZZA_E_TEST.md): invarianti e prove da non perdere.
6. [Operazioni e manutenzione](OPERAZIONI_E_MANUTENZIONE.md): diagnosi, backup,
   reset e rilascio.
7. [Riferimento comandi](RIFERIMENTO_COMANDI.md): sintassi CLI e script.

## Sorgenti canoniche

| Area | Percorso | Responsabilita` |
| --- | --- | --- |
| Adapter Google | `apps_script/src/` | form, Drive, Da archiviare, Registro e notifiche Google |
| Connettore locale | `local_connector/src/virgilio_connector/` | IMAP, quarantena, scansione, stato, consegna e ack |
| Applicazione utente | `local_connector/src/virgilio_connector/user_app/` | Caronte in linguaggio utente |
| Servizi condivisi | `local_connector/src/virgilio_connector/application/` | casi d'uso condivisi da GUI e CLI |
| Test offline | `local_connector/tests/` | unita`, contratti e integrazioni senza servizi reali |
| Automazione locale | `scripts/dev/` | bootstrap, test, smoke, build e installer |

Le regole per contribuire e i documenti Codex sono separati in
[`docs/sviluppo/`](../sviluppo/README.md).
