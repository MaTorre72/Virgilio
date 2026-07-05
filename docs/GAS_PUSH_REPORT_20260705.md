# GAS push report Virgilio - 2026-07-05

## 1. Esito

- esito: GO
- motivo: il mirror `apps_script/clasp` e` stato ricostruito da `apps_script/src`, il progetto GAS live e` stato ripushato e la distribuzione web `@28` e` stata aggiornata alla v1.1.3
- vincolo rispettato: nessun intervento su `.clasprc.json`, credenziali o dati operativi reali
- base canonica scelta: `apps_script/src`

## 2. Verifica di affidabilita`

- una lettura live preliminare con `clasp pull` aveva mostrato il progetto remoto ancora fermo al mirror vecchio
- il confronto file-per-file tra `apps_script/src` e `apps_script/clasp` e` stato usato come base tecnica affidabile per la sync
- il push forzato ha riallineato il progetto remoto ai file canonici presenti in `src`

## 3. Sync e deploy

- mirror ricostruito da `apps_script/src` verso `apps_script/clasp`
- file legacy P3/P4 rimossi dal mirror di lavoro prima del push
- `clasp push -f` completato con 13 file
- versione Apps Script creata: `28`
- distribuzione aggiornata: `AKfycbzp-LolcYoZwsq0j--znV8szZ-N0SRkCLo9z1R5ahtr12lgapEWWrxJyaRFyG9wC_Y4Sg @28 - Virgilio v1.1.3 GAS bridge`

## 4. Verifiche finali

- confronto `src` vs `clasp`: tutti i file canonici corrispondono
- `git status --short`: pulito
- `clasp deployments`: `@HEAD` presente e distribuzione versionata aggiornata a `@28`

## 5. Nota operativa

- la matrice del 2026-07-04 era utile come fotografia storica, ma il live pull ha mostrato che il remoto era ancora sul mirror vecchio
- la sorgente canonica resta `apps_script/src` e il mirror pubblico va sempre riallineato da li` prima del deploy
