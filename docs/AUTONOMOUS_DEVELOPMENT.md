# Sviluppo autonomo

## Selezione e avanzamento

Codex legge `AGENTS.md`, quindi sceglie in `DEV_BACKLOG.md` il primo task P0/P1 con stato `TODO`,
prerequisiti soddisfatti e rischio compatibile con test locali. Si lavora su un task per run.
Bugfix bloccanti il pilota precedono feature; hardening precede usabilità; documentazione isolata
si esegue solo quando sblocca uso o manutenzione.

## Autonomia consentita

Codex può leggere codice, modificare repository, usare fixture/fake, eseguire test, aggiornare backlog
e creare commit sulla branch di sviluppo. Non chiede chiarimenti quando il comportamento più semplice
e prudente è deducibile dai test e dai contratti esistenti.

Si ferma per credenziali o permessi reali, working tree non spiegato, modifiche irreversibili, conflitti
di requisiti, mail/Google reali non autorizzati o decisioni di prodotto con alternative sostanziali.

## Chiusura run

Aggiornare stato, evidenze e commit nel backlog; eseguire smoke e suite; controllare segreti; committare.
Un fallimento CI diventa bugfix prioritario. Il prompt `advance.md` avanza il backlog, `fix-ci.md` ripara
la CI, `review.md` verifica la DoD e `pilot-hardening.md` migliora solo affidabilità.

Le automazioni devono essere seriali e distanziate: una run principale ogni almeno 5 ore, massimo tre
run pianificate al giorno e revisione settimanale prima di consumare ulteriore capacità. Se il prodotto
non espone il credito residuo, non stimarlo: usare questa cadenza conservativa e fermarsi dopo un task.

Una Codex Action automatica non è attivata: richiederebbe segreti e una policy PR dedicata. I prompt
sono pronti per un'eventuale attivazione manuale futura.

