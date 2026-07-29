# Documentazione Virgilio 1.1

Questo e` l'unico ingresso alla documentazione corrente. I contenuti sono
separati per pubblico: chi usa Virgilio non deve attraversare backlog o note
Codex, mentre chi sviluppa trova architettura, contratti, comandi e storia
operativa in percorsi espliciti.

## Voglio usare Virgilio

Vai al [manuale utente](utente/README.md).

- [Primo avvio](utente/PRIMO_AVVIO.md): cosa preparare e come completare la
  configurazione guidata.
- [Uso quotidiano](utente/USO_QUOTIDIANO.md): dalla mail alla pratica finale.
- [Risoluzione dei problemi](utente/RISOLUZIONE_PROBLEMI.md): messaggi,
  controlli sicuri e quando serve manutenzione.
- [Manuale completo](utente/MANUALE.md): panoramica e percorso di lettura.

## Devo installare, amministrare o capire il sistema

Vai alla [documentazione tecnica](tecnica/README.md).

- [Architettura](tecnica/ARCHITETTURA.md): componenti, responsabilita`, flussi
  e confini.
- [Modello dati e stati](tecnica/MODELLO_DATI_E_STATI.md): identita`, SQLite,
  Da archiviare, Registro e transizioni.
- [Installazione e comandi](tecnica/INSTALLAZIONE_E_COMANDI.md): prerequisiti,
  ambiente, test e build.
- [Configurazione e integrazioni](tecnica/CONFIGURAZIONE_E_INTEGRAZIONI.md):
  IMAP, Drive Desktop, Apps Script, Registro e notifiche.
- [Operazioni e manutenzione](tecnica/OPERAZIONI_E_MANUTENZIONE.md): diagnosi,
  backup, reset, release e recupero.
- [Riferimento comandi](tecnica/RIFERIMENTO_COMANDI.md): CLI e script
  effettivamente disponibili.
- [Sicurezza e test](tecnica/SICUREZZA_E_TEST.md): minacce, controlli e livelli
  di verifica offline.

## Devo continuare lo sviluppo

Vai alla [documentazione di sviluppo](sviluppo/README.md).

- [Come contribuire](sviluppo/CONTRIBUIRE.md): orientamento, workflow e criteri
  di modifica.
- [Roadmap 1.1](sviluppo/ROADMAP_1_1.md): roadmap originale A-H aggiornata allo
  stato realmente raggiunto.
- `CODEX_STATE.md`, `NEXT_CODEX_TASKS.md`, `DEV_BACKLOG.md` e gli altri file
  nella stessa cartella sono documenti interni per sviluppo e automazioni.

## Regole della struttura

- Al livello `docs/` vive soltanto questo indice.
- `docs/utente/` non contiene comandi interni, contratti o cronologia di
  sviluppo.
- `docs/tecnica/` descrive la release ufficiale 1.1 e i suoi vincoli reali.
- `docs/sviluppo/` contiene governance, roadmap, backlog, evidenze e storia.
