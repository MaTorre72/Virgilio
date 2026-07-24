# Next Codex Tasks

- Iniziativa: `GUI-U = IN_PROGRESS`.
- Fase: `GUI-U-R - Recupero prodotto e collaudo osservabile`.
- Task completati: `GUI-U-R01`, `GUI-U-R02-T02`, `GUI-U-R03-T01`. `GUI-U-R02-T01` e `T03` restano evidenze storiche `IMPLEMENTED_NOT_ACCEPTED`.
- R02: `SUPERSEDED_BY_R3` dopo il `FAIL` umano del demo. Il demo non viene ampliato o ricollaudato; tutti i requisiti `H-R02-01`--`H-R02-08` sono trasferiti a R3 e restano obbligatori.
- Fascicolo: `artifacts/gui-u-r02/f7eb037d-924e-4a04-b9a9-3f2751137a42/` (ignorato): build/release manifest, SHA-256, dieci screenshot installati, checklist e istruzioni.
- Riscontro: con installazione pulita Caselle non permette di aggiungere dati demo e non consente di arrivare a Riepilogo/Home; il pulsante osservato e` `Termina configurazione` invece di `Completa configurazione`. Google non e` configurato per scelta e non deve esserlo in R02.
- Decisione: il demo non viene ampliato; viene mantenuto solo per evidenze interne. La priorita` e` un percorso operativo reale.
- Task completati: `GUI-U-R03-T01 - Prima casella reale senza blocco Google`, `GUI-U-R03-T02 - Seconda casella e verifica collegamento` e `GUI-U-R03-T03 - Percorso reale completo, Riepilogo e Home`; il Riepilogo reale conserva Limbo/caselle, indica correzioni e porta a Home (`39 passed`, fixture fake e Tk reale).
- Esito corrente: `GUI-U-R03 - Collaudo umano unico della build operativa` = `FAIL` su `H-R03-02`. La nuova build `bb9b16e`, ID `9337fa8d-737e-4b16-8f82-b68cb129c778`, supera OAuth e verifica read-only su `INBOX`, ma non aggiunge la casella.
- Task completato: `GUI-U-R03-R01 - Verifica collegamento su INBOX`. `AccountConnectionRequest` dichiara `INBOX`, il servizio la passa all'adapter read-only e la regressione che rifiuta la cartella operativa implicita e` verde; gruppo mirato R03-R01/R03-T02 `15 passed`.
- Task completato: `GUI-U-R03-R02 - Cartelle operative configurabili per casella`. La GUI espone nelle impostazioni avanzate cartella da controllare, completati e problemi; valori obbligatori, distinti per casella e persistenti su aggiunta/modifica/riapertura. Caso `da-traghettare` senza cartella madre verde; check R03-R01 ancora su `INBOX`; core `17 passed`, Tk interessato `1 passed`.
- Diagnosi read-only: configurazione assente, entrambi i riferimenti protetti `Principale` gia` presenti. Il percorso `add` create-only solleva un errore non gestito e lascia in GUI il precedente successo. `25 messaggi visibili` e` il limite del campione, non il totale. L'utente giudica astrusa la sequenza verifica/aggiunta.
- Successivo univoco proposto, in attesa di approvazione: `GUI-U-R03-R03 - Collegamento casella guidato e salvataggio recuperabile`. Una sola azione per provider autorizza/verifica e salva; gli errori di persistenza sono visibili e recuperabili; il campione non e` presentato come totale. Nessuna nuova build prima della chiusura.
- Le evidenze gia` acquisite restano valide e non devono essere ripetute; ogni run aggiunge soltanto la prova specifica del nuovo criterio.
- Il collaudo R3 riprende dalla prima evidenza non acquisita solo dopo build identificata del correttivo approvato; le evidenze valide gia` raccolte non vengono ripetute.

Dettagli, criteri ed evidenze: `docs/GUI_U_BACKLOG.md` e
`docs/GUI_U_HUMAN_ACCEPTANCE.md`.
