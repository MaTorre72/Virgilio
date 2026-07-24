# Next Codex Tasks

- Iniziativa: `GUI-U = IN_PROGRESS`.
- Fase: `GUI-U-R - Recupero prodotto e collaudo osservabile`.
- Task completati: `GUI-U-R01`, `GUI-U-R02-T02`, `GUI-U-R03-T01`. `GUI-U-R02-T01` e `T03` restano evidenze storiche `IMPLEMENTED_NOT_ACCEPTED`.
- R02: `SUPERSEDED_BY_R3` dopo il `FAIL` umano del demo. Il demo non viene ampliato o ricollaudato; tutti i requisiti `H-R02-01`--`H-R02-08` sono trasferiti a R3 e restano obbligatori.
- Fascicolo: `artifacts/gui-u-r02/f7eb037d-924e-4a04-b9a9-3f2751137a42/` (ignorato): build/release manifest, SHA-256, dieci screenshot installati, checklist e istruzioni.
- Riscontro: con installazione pulita Caselle non permette di aggiungere dati demo e non consente di arrivare a Riepilogo/Home; il pulsante osservato e` `Termina configurazione` invece di `Completa configurazione`. Google non e` configurato per scelta e non deve esserlo in R02.
- Decisione: il demo non viene ampliato; viene mantenuto solo per evidenze interne. La priorita` e` un percorso operativo reale.
- Task completati: `GUI-U-R03-T01 - Prima casella reale senza blocco Google`, `GUI-U-R03-T02 - Seconda casella e verifica collegamento` e `GUI-U-R03-T03 - Percorso reale completo, Riepilogo e Home`; il Riepilogo reale conserva Limbo/caselle, indica correzioni e porta a Home (`39 passed`, fixture fake e Tk reale).
- Esito corrente: `GUI-U-R03 - Collaudo umano unico della build operativa` = `FAIL` su `H-R03-02`. La build `1ad484b` completa OAuth, XOAUTH2, apertura read-only di `INBOX`, ricerca e lettura di 100 messaggi; la GUI fallisce perche` la verifica seleziona implicitamente la cartella operativa `Virgilio/da-traghettare`, assente sulla casella.
- Successivo univoco proposto, in attesa di approvazione: `GUI-U-R03-R01 - Verifica collegamento su INBOX`. Risultato: la sola verifica di connettivita` usa `INBOX`, senza dipendere da cartelle operative nascoste; massimo tre criteri: richiesta esplicita `INBOX`, regressione fake sul fallimento riprodotto, prove mirate R03-T02 verdi; componenti: `AccountConnectionRequest`, servizio read-only e test mirati; esclusioni: credenziali/rete reali nei test, redesign, Apps Script e altre operazioni casella; blocco: il check non puo` restare read-only o richiede configurazione utente aggiuntiva.
- Le evidenze gia` acquisite restano valide e non devono essere ripetute; ogni run aggiunge soltanto la prova specifica del nuovo criterio.
- Il collaudo R3 riprende dalla prima evidenza non acquisita solo dopo build identificata del correttivo approvato; le evidenze valide gia` raccolte non vengono ripetute.

Dettagli, criteri ed evidenze: `docs/GUI_U_BACKLOG.md` e
`docs/GUI_U_HUMAN_ACCEPTANCE.md`.
