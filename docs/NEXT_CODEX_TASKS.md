# Next Codex Tasks

- Iniziativa: `GUI-U = IN_PROGRESS`.
- Fase: `GUI-U-R - Recupero prodotto e collaudo osservabile`.
- Task completati: `GUI-U-R01`, `GUI-U-R02-T02`, `GUI-U-R03-T01`. `GUI-U-R02-T01` e `T03` restano evidenze storiche `IMPLEMENTED_NOT_ACCEPTED`.
- R02: `SUPERSEDED_BY_R3` dopo il `FAIL` umano del demo. Il demo non viene ampliato o ricollaudato; tutti i requisiti `H-R02-01`--`H-R02-08` sono trasferiti a R3 e restano obbligatori.
- Fascicolo: `artifacts/gui-u-r02/f7eb037d-924e-4a04-b9a9-3f2751137a42/` (ignorato): build/release manifest, SHA-256, dieci screenshot installati, checklist e istruzioni.
- Riscontro: con installazione pulita Caselle non permette di aggiungere dati demo e non consente di arrivare a Riepilogo/Home; il pulsante osservato e` `Termina configurazione` invece di `Completa configurazione`. Google non e` configurato per scelta e non deve esserlo in R02.
- Decisione: il demo non viene ampliato; viene mantenuto solo per evidenze interne. La priorita` e` un percorso operativo reale.
- Task completati: `GUI-U-R03-T01 - Prima casella reale senza blocco Google` e `GUI-U-R03-T02 - Seconda casella e verifica collegamento`; due caselle mantengono credenziali distinte, CRUD e persistenza e la verifica usa feedback asincrono con adapter fake (`12 passed`).
- Task corrente univoco: `GUI-U-R03-T03 - Percorso reale completo, Riepilogo e Home`, che assorbe i requisiti UX R2 non ancora dimostrati sul prodotto reale.
- Le evidenze gia` acquisite restano valide e non devono essere ripetute; ogni run aggiunge soltanto la prova specifica del nuovo criterio.
- Un solo collaudo umano R3, sulla build operativa completa, verifica insieme servizi reali e requisiti UX ereditati da R2.

Dettagli, criteri ed evidenze: `docs/GUI_U_BACKLOG.md` e
`docs/GUI_U_HUMAN_ACCEPTANCE.md`.
