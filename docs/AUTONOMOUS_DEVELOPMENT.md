# Sviluppo autonomo

## Selezione e avanzamento

Codex legge `AGENTS.md`, quindi sceglie in `docs/DEV_BACKLOG.md` il primo task P0/P1 con stato `TODO`,
prerequisiti soddisfatti e rischio compatibile con test locali. Si lavora su un task per run.
Bugfix bloccanti il pilota precedono feature; hardening precede usabilita; documentazione isolata si
esegue solo quando sblocca uso o manutenzione.

Se il backlog contiene un task 0.0, quel task ha priorita assoluta sui task successivi di v1.1.3.
Non si avanza oltre finche la separazione tra sorgente Apps Script e snapshot `clasp` non e` stata
completata e verificata.

## Cadenza oraria

L`automazione "Virgilio sviluppo autonomo" parte ogni ora. Ogni esecuzione deve essere indipendente,
seriale e non sovrapposta: se la run precedente non e` chiusa, la nuova run deve fermarsi senza avviare
un secondo task.

## Autonomia consentita

Codex puo leggere codice, modificare repository, usare fixture/fake, eseguire test, aggiornare backlog
e creare commit sulla branch di sviluppo. Non chiede chiarimenti quando il comportamento piu semplice
e prudente e` deducibile dai test e dai contratti esistenti.

Si ferma per credenziali o permessi reali, working tree non spiegato, modifiche irreversibili, conflitti
di requisiti, mail/Google reali non autorizzati o decisioni di prodotto con alternative sostanziali.

Per essere pronto alla piena autonomia, il workspace deve restare leggibile, senza mescolare nella stessa
cartella le due rappresentazioni del progetto Apps Script. La separazione tra sorgente canonica e snapshot
`clasp` e` parte del lavoro autonomo, non un dettaglio cosmetico.

## Chiusura run

Aggiornare stato, evidenze e commit nel backlog; eseguire smoke e suite quando il task tocca codice;
controllare segreti; committare. Un fallimento CI diventa bugfix prioritario. Il prompt `advance.md`
avanza il backlog, `fix-ci.md` ripara la CI, `review.md` verifica la DoD e `pilot-hardening.md`
migliora solo affidabilita.

Le automazioni devono essere seriali: una run alla volta, senza sovrapposizioni.
Se il prodotto non espone il credito residuo, non stimarlo; usare questa cadenza conservativa e
fermarsi dopo un task.

Una Codex Action automatica non e` attivata: richiederebbe segreti e una policy PR dedicata. I prompt
sono pronti per un`eventuale attivazione manuale futura.
