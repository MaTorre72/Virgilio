# Definition of Done

## Prima di iniziare un task

Ogni task deve avere:

- risultato concreto;
- massimo cinque criteri binari;
- prova prevista per ogni criterio;
- dipendenze;
- componenti ammessi;
- esclusioni;
- condizione di blocco.

Se manca uno di questi elementi, il task non entra in `IN_PROGRESS`.

## Regole anti-loop

1. Un task deve chiudersi in una singola run.
2. Se e` troppo grande, deve essere suddiviso prima di modificare codice.
3. La run deve chiudere tutti i criteri del task.
4. Se zero criteri avanzano, non viene creato un commit di codice.
5. Se emerge un blocco, il codice parziale viene annullato e il task passa a `BLOCKED`.
6. Dopo due blocchi con la stessa causa, non viene effettuato un terzo tentativo automatico.
7. Sono vietati polishing e refactor non collegati a un criterio.
8. Un criterio chiuso si riapre solo con una regressione riproducibile.
9. Quando tutti i criteri sono soddisfatti, il task viene chiuso nella stessa run.
10. Miglioramenti ulteriori diventano nuovi task.

## Evidenze

Le evidenze devono essere registrate direttamente nella scheda del task nel
backlog operativo corrente con questo formato:

| Criterio | Prova prevista | Evidenza ottenuta | Esito |
| -------- | -------------- | ----------------- | ----- |

Una suite genericamente verde non sostituisce l'evidenza specifica associata a
ciascun criterio.

## Verifica umana

Codex non puo` dichiarare autonomamente `PASS`:

- `GATE U-H1`;
- `GATE U-H2`;
- `GATE U-H3`.

Questi gate restano `WAITING_HUMAN_REVIEW` fino a conferma esplicita.

## Termini vietati nella GUI utente

Salvo una sezione tecnica avanzata esplicitamente prevista, nella GUI utente non devono comparire:

- Python;
- venv;
- CLI;
- YAML;
- `.env`;
- doctor;
- pilot;
- dry-run;
- watch;
- staging;
- ack;
- manifest;
- SQLite;
- exit code;
- account_alias;
- username_env;
- password_env;
- stack trace;
- percorso del repository.

Deve esistere un test automatico sulle stringhe visibili della GUI utente.

## Chiusura del task

Un task e` `DONE` solo quando tutti i criteri hanno evidenza specifica con esito positivo,
i test richiesti dal suo ambito sono verdi, diff e stato Git sono verificati, nessun segreto
e` tracciato e i puntatori operativi sono aggiornati. Un task bloccato resta non completato
e registra causa, evidenza e singola azione necessaria.

Il riepilogo finale della run non supera 12 righe.
