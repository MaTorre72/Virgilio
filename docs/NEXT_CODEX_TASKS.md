# Next Codex Tasks

- Iniziativa: `GUI-U = IN_PROGRESS`.
- Fase: `GUI-U-R - Recupero prodotto e collaudo osservabile`.
- Task completati: `GUI-U-R01`, `GUI-U-R02-T02`, `GUI-U-R03-T01`. `GUI-U-R02-T01` e `T03` restano evidenze storiche `IMPLEMENTED_NOT_ACCEPTED`.
- R02: `SUPERSEDED_BY_R3` dopo il `FAIL` umano del demo. Il demo non viene ampliato o ricollaudato; tutti i requisiti `H-R02-01`--`H-R02-08` sono trasferiti a R3 e restano obbligatori.
- Fascicolo: `artifacts/gui-u-r02/f7eb037d-924e-4a04-b9a9-3f2751137a42/` (ignorato): build/release manifest, SHA-256, dieci screenshot installati, checklist e istruzioni.
- Riscontro: con installazione pulita Caselle non permette di aggiungere dati demo e non consente di arrivare a Riepilogo/Home; il pulsante osservato e` `Termina configurazione` invece di `Completa configurazione`. Google non e` configurato per scelta e non deve esserlo in R02.
- Decisione: il demo non viene ampliato; viene mantenuto solo per evidenze interne. La priorita` e` un percorso operativo reale.
- Task completati: `GUI-U-R03-T01 - Prima casella reale senza blocco Google`, `GUI-U-R03-T02 - Seconda casella e verifica collegamento` e `GUI-U-R03-T03 - Percorso reale completo, Riepilogo e Home`; il Riepilogo reale conserva Limbo/caselle, indica correzioni e porta a Home (`39 passed`, fixture fake e Tk reale).
- Esito corrente: `GUI-U-R03 - Collaudo umano unico della build operativa` = `DONE`. `H-R03-01`--`H-R03-06 = PASS` umano; `R03-AC1`--`R03-AC5 = MET`.
- Task completato: `GUI-U-R03-R01 - Verifica collegamento su INBOX`. `AccountConnectionRequest` dichiara `INBOX`, il servizio la passa all'adapter read-only e la regressione che rifiuta la cartella operativa implicita e` verde; gruppo mirato R03-R01/R03-T02 `15 passed`.
- Task completato: `GUI-U-R03-R02 - Cartelle operative configurabili per casella`. La GUI espone nelle impostazioni avanzate cartella da controllare, completati e problemi; valori obbligatori, distinti per casella e persistenti su aggiunta/modifica/riapertura. Caso `da-traghettare` senza cartella madre verde; check R03-R01 ancora su `INBOX`; core `17 passed`, Tk interessato `1 passed`.
- Diagnosi read-only: configurazione assente, entrambi i riferimenti protetti `Principale` gia` presenti. Il percorso `add` create-only solleva un errore non gestito e lascia in GUI il precedente successo. `25 messaggi visibili` e` il limite del campione, non il totale. L'utente giudica astrusa la sequenza verifica/aggiunta.
- Task completato: `GUI-U-R03-R03 - Collegamento casella guidato e salvataggio recuperabile`. Google usa `Collega con Google`, IMAP usa `Verifica e aggiungi`; al successo la casella viene salvata e appare nell'elenco. Riferimenti orfani riconciliati con rollback, errori sicuri e testo del campione rimosso; core `37 passed`, Tk interessato `1 passed`.
- Build R03-R03 pronta: `CaronteSetup-0.11.0-8241325.exe`, commit `8241325bf96d858259a577c87ffaba8c25513a05`, ID `7dcae8b2-5bd2-47b6-9c89-f53b4cf4c1ff`, SHA-256 `79BC5677B21B29CAF3F7E07A9394072FBBBA446DA573FF5AF0181B8CFF260FF8`; client OAuth Desktop incorporato, smoke build e installer `PASS`.
- Diagnosi `H-R03-06`: Registro non configurato e attivazione automatica sono indipendenti. La configurazione utente non contiene ancora il Registro; il controllo automatico fallisce invece creando con `schtasks` un'attivita che non risulta installata.
- Task completato: `GUI-U-R03-R04 - Controllo automatico per utente`. Il worker congelato e` registrato in `Run` per il solo utente corrente, senza Task Scheduler, UAC o privilegi amministrativi; Registro e controllo automatico restano indipendenti e la disinstallazione pulisce registrazioni nuova e legacy. Mirati `27 passed`, smoke locale `504 passed`, build/installer identificati e smoke `PASS`.
- Ripresa R03-R04: `H-R03-06 = PASS` umano esplicito sulla build `eaf05fd`, ID `0c40a31d-ee7a-4d8c-9f0d-5ff795fb5b39`; attivazione, stato, persistenza dopo nuovo accesso Windows, disattivazione e assenza di finestre tecniche tutti confermati.
- Chiusura R03: `H-R03-01 = PASS` umano esplicito; selezione, validazione, salvataggio, ritorno, riapertura, persistenza e modifica del Limbo approvati. Osservazione non bloccante: i campi degli indirizzi cartella sono troppo piccoli.
- Task completato: `GUI-U-R03-R05 - Campi cartella leggibili`. Limbo nel primo avvio e in Impostazioni e le tre cartelle operative avanzate usano larghezza minima di 48 caratteri e colonne elastiche; valori lunghi scorrono e conservano selezione/copia/incolla. Gruppo mirato `47 passed`, Tk entro 960x640 a 100%/125%, smoke locale `506 passed`.
- Successivo univoco: definire e sottoporre ad approvazione un correttivo finito per il difetto separato del disinstallatore diretto prima della release; non modificare codice senza approvazione.
- Le evidenze gia` acquisite restano valide e non devono essere ripetute; ogni run aggiunge soltanto la prova specifica del nuovo criterio.
- Il collaudo R3 riprende dalla prima evidenza non acquisita solo dopo build identificata del correttivo approvato; le evidenze valide gia` raccolte non vengono ripetute.

Dettagli, criteri ed evidenze: `docs/GUI_U_BACKLOG.md` e
`docs/GUI_U_HUMAN_ACCEPTANCE.md`.
