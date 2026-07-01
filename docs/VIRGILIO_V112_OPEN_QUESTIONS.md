# Virgilio v1.1.2 - Supporto sintetico per le decisioni aperte

Riferimento principale: [docs/VIRGILIO_V112_INTEGRATION_ROADMAP.md](./VIRGILIO_V112_INTEGRATION_ROADMAP.md)

## Obiettivo

Questo foglio serve per studiare rapidamente le domande aperte prima di scegliere il ponte finale Caronte -> Virgilio.

## 1. Ponte temporaneo o permanente?

Opzioni:

- A. Temporaneo, solo per transizione verso v1.1
- B. Permanente, come inbox tecnico stabile
- C. Ibrido, temporaneo ora e rivalutato dopo il primo pilota

Scelta consigliata:

- C, perche` lascia aperta la decisione architetturale senza bloccare il flusso.

Rischio principale:

- se lo si tratta come permanente troppo presto, si consolida un adattatore non ancora validato.

## 2. `Virgilio_Inbox` nuovo tab o tab esistente?

Opzioni:

- A. Nuovo tab `Virgilio_Inbox`
- B. Riuso di `Staging_Local_Test`
- C. Riuso di `bucoliche` con una sezione tecnica separata

Scelta consigliata:

- A, per separare bene inbox tecnico, produzione e test.

Rischio principale:

- il riuso del tab test o del tab operativo aumenta la confusione tra dati umani e dati macchina.

## 3. Matching allegato-pratica: automatico o umano?

Opzioni:

- A. Automatico subito
- B. Umano all'inizio, automatico solo dopo una prova
- C. Manuale definitivo

Scelta consigliata:

- B, con regole semplici e conferma umana finche` i casi reali non sono stabili.

Rischio principale:

- matching automatico troppo presto puo` associare allegati alla pratica sbagliata.

## 4. `Bucoliche`: solo registro o anche inbox?

Opzioni:

- A. Solo registro operativo storico
- B. Registro + inbox tecnico
- C. Solo inbox tecnico, nuovo schema

Scelta consigliata:

- A, lasciando l'inbox a un tab separato.

Rischio principale:

- mescolare inbox e registro rende piu` difficile audit, debug e manutenzione.

## 5. `Staging_Local_Test`: solo test o riferimento di contratto?

Opzioni:

- A. Solo test
- B. Test + riferimento di contratto
- C. Diventa la base del flusso operativo

Scelta consigliata:

- B, come riferimento utile per i controlli ma non come tab operativo.

Rischio principale:

- se diventa operativo, si perde la separazione tra validazione e produzione.

## Decisione pratica breve

Se serve una risposta veloce:

- ponte: temporaneo ma disciplinato;
- tab: `Virgilio_Inbox` nuovo;
- matching: umano prima, automatico dopo;
- `Bucoliche`: registro, non inbox;
- `Staging_Local_Test`: riferimento di contratto, non produzione.

