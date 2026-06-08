# 🌿 Progetto Virgilio — Sistema di archiviazione intelligente per Sigma+
**versione 1.0 — mono-utente**
*ultimo aggiornamento: giugno 2025*

---

## Cosa fa questo sistema (il problema che risolve)

Sigma+ è uno studio di consulenza ambientale ed economia circolare. Nel lavoro quotidiano arrivano continuamente email con allegati tecnici: planimetrie, autorizzazioni, relazioni, moduli — documenti che devono essere archiviati nelle cartelle giuste su Google Drive, assegnati alla commessa corretta, e resi disponibili ai colleghi che seguono quella pratica.

Fino ad oggi questo processo era manuale: ogni tecnico archiviava come preferiva, senza un preciso standard condiviso, e il passaggio di informazioni al team avveniva in modo informale (email inoltrate, messaggi su WhatsApp, avvisi verbali). Il risultato era un archivio disomogeneo, difficile da consultare, e un flusso di comunicazione interna spesso dipendente dalla memoria delle singole persone.

**Virgilio risolve questo problema** automatizzando i due passaggi più critici del flusso:

1. **L'archiviazione** — gli allegati delle email vengono depositati automaticamente nella cartella Drive corretta, seguendo uno standard di nomenclatura condiviso (`Cliente/Sito/Anno_TipoPratica`)
2. **La comunicazione interna** — quando viene aperta una nuova pratica o arriva del materiale, il team viene avvisato automaticamente con un messaggio strutturato che contiene il link diretto alla cartella

Il tecnico fa un solo gesto intenzionale (compilare il form o aggiungere un'etichetta alla mail). Il resto lo fa Virgilio.

> **Nota v1.0 — mono-utente.** In questa versione il sistema scansiona la sola casella `marco@sigmapiu.it`. L'estensione alle caselle degli altri tecnici del team è pianificata per la v1.1.

---

## Chi usa questo sistema

| Ruolo | Come interagisce con Virgilio |
|---|---|
| **Tecnico referente** | Compila il form di apertura pratica o etichetta la mail in Gmail |
| **Team tecnico** | Riceve la notifica su Google Chat e/o Telegram con il link alla cartella |
| **Amministratore di sistema** | Gestisce la configurazione, i permessi, e gli aggiornamenti del codice |
| **Colleghi non tecnici** | Non interagiscono con il codice — usano solo il form e leggono le notifiche |

Il sistema è progettato per essere usato da **persone non programmatori nella loro routine quotidiana**. L'unico punto che richiede competenze informatiche è la configurazione e la manutenzione del codice, gestita da chi amministra il progetto.

---

## Confini della versione 1.0

### ✅ Cosa è dentro questa versione

- **Caronte** — lo script Apps Script che scansiona la casella Gmail di `marco@sigmapiu.it`, trova le mail etichettate `da-traghettare`, e salva gli allegati reali (escluse immagini di firma, file di servizio e allegati troppo piccoli) nel **Limbo**, una cartella temporanea in attesa di assegnazione. Il trigger gira automaticamente ogni 5 minuti.

- **Form di apertura pratica (Virgilio)** — interfaccia web a 4 step con menu a tendina per cliente e sito (popolati dinamicamente dall'anagrafica), tipo pratica (vocabolario controllato: AUA, AIA, VIA, EoW, TR, bonifica, emissioni, rifiuti, sottoprodotti, PEI, PEE, reportAIA, assistenza), anno, selezione tecnici e campo note. Accessibile da browser anche mobile.

- **Creazione automatica cartella Drive** — a partire dai dati del form, Caronte copia **Adamo** (il template) e crea la struttura standard `Cliente/Sito/Anno_TipoPratica` con le sotto-cartelle obbligatorie (`00_autorizzazioni`, `01_dati-ditta`, `02_corrispondenza`) dentro l'**Empireo**.

- **Spostamento allegati Limbo → pratica** — dopo l'apertura pratica, Caronte sposta automaticamente gli allegati recenti dal Limbo nella cartella `02_corrispondenza` del sito. Il matching è temporale (finestra configurabile, default 2 giorni).

- **Notifiche al team** — messaggi automatici separati e ottimizzati per Google Chat (Markdown) e Telegram (HTML con link cliccabili). La notifica di traghettamento include mittente, oggetto e nomi file. La notifica di apertura pratica include cliente, sito, pratica, tecnici e link diretto alla cartella Drive.

- **Bucoliche** — registro completo su Google Sheets a 17 colonne. Le prime 10 colonne registrano i dati operativi (timestamp, origine, cliente, sito, pratica, anno, tecnici, note, url cartella, id Drive). Le colonne 11-17 raccolgono i metadati ML per il futuro classificatore (mittente dominio, oggetto email, nome file, estensione, dimensione KB, stato, timestamp archiviazione). Le righe `gmail_staging` vengono aggiornate in-place a `gmail_archiviato` quando il file viene assegnato, senza duplicazioni.

- **Anagrafica integrata** — il file Bucoliche ospita tre tab di riferimento: `Clienti_Siti` (coppie cliente/sito, alimentato dal form), `Team` (tecnici Sigma+), `TipiPratica` (vocabolario pratiche con descrizioni). I dropdown del form Virgilio si popolano dinamicamente da questi tab. In v1.1 sarà aggiunto uno script di sincronizzazione con VTEnext.

- **Security audit completo** — tutte le credenziali in PropertiesService (mai nel codice), XSS fix su innerHTML, null-check token, rate limiting su doPost(), validazione lunghezze campi, sanitizzazione nomi file, privacy sul logging.

### ❌ Cosa è fuori da questa versione

- **Scansione multi-utente** — nella v1.0 viene scansionata solo la casella `marco@sigmapiu.it`. Aggiungere le caselle degli altri tecnici è il primo passo della v1.1.
- **Integrazione VTEnext webhook** — il punto di ingresso tramite BPM di VTEnext è architetturalmente previsto (endpoint `doPost()` già pronto), ma la configurazione lato CRM è rimandata alla v1.1.
- **Classificazione automatica delle email** — nella v1.0 il tecnico indica esplicitamente a quale commessa appartiene la mail. Il classificatore AI che suggerisce cliente e pratica è previsto dalla v2.0 (i dati ML vengono già raccolti nelle Bucoliche come training set).
- **Gestione delle scadenze** — può essere facilmente sviluppato un guardiano automatico delle scadenze autorizzative (AUA 15 anni, AIA 10 anni, reportAIA annuali).
- **Beatrice (fatture e pagamenti)** — un modulo che gestisce la parte economica delle commesse.
- **Estrazione automatica di dati dai documenti** — lettura di PDF con estrazione di prescrizioni, limiti, date.
- **Knowledge base interrogabile** — possibilità di fare domande in linguaggio naturale sull'archivio commesse.
- **Migrazione commesse storiche** — le cartelle cliente esistenti nell'Empireo non vengono toccate né migrate automaticamente.

---

## La cosmologia del sistema

Il progetto si ispira liberamente alla *Divina Commedia* di Dante e alle opere di Virgilio — scelta non casuale per il territorio Verona-Mantova. Ogni componente ha un nome ispirato che evoca la sua funzione nel flusso di lavoro.

### I personaggi

| Nome | Tipo | Funzione |
|---|---|---|
| **Virgilio** | Bot / Sistema | La guida — orienta il tecnico, fa le domande giuste |
| **Caronte** | Script Apps Script | Il traghettatore — prende gli allegati e li porta dove devono stare |
| **Beatrice** | Sistema futuro | Fatture, pagamenti, la visione economica — il Paradiso ancora da costruire |

### I luoghi

| Nome | Dove | Cosa contiene |
|---|---|---|
| **Empireo** | Cartella Drive radice | `01_commesse_Sigma+` — il cielo più alto, contiene tutto l'archivio |
| **Adamo** | Cartella template | Il prototipo da copiare per ogni pratica nuova — il primo, da cui discendono tutti |
| **Limbo** | Cartella temporanea Drive | Gli allegati arrivati ma non ancora assegnati — in attesa, sospesi |

### Gli stati delle pratiche

| Nome | Stato | Quando si usa |
|---|---|---|
| **Selva** | In corso | Pratica aperta, si sta lavorando — *nel mezzo del cammin* |
| **Purgatorio** | In attesa | Pratica avviata, in attesa di risposta da ente o cliente |
| **Paradiso** | Conclusa | Pratica chiusa con successo, autorizzazione ottenuta |
| **Inferno** | Bloccata | Pratica con problemi seri, contenziosa, sospesa d'autorità |
| **Bolgia** | Abbandonata | Pratica congelata a tempo indeterminato, nel dimenticatoio |

### Le etichette Gmail

| Nome | Etichetta | Funzione |
|---|---|---|
| `da-traghettare` | Trigger | Il tecnico la aggiunge alla mail da archiviare — Caronte la trova |
| `traghettate` | Post-elaborazione | Caronte la aggiunge dopo aver processato la mail — il viaggio è fatto |

### Il registro

| Nome | Strumento | Funzione |
|---|---|---|
| **Bucoliche** | Google Sheets | Registro di ogni operazione (17 colonne) + anagrafica clienti, team e pratiche nei tab di riferimento |

---

## L'idea generale e i possibili sviluppi futuri

Virgilio nasce da una constatazione semplice: in uno studio di consulenza piccolo, il vero collo di bottiglia non è la capacità tecnica delle persone — è il **costo cognitivo di fare le cose per bene**. Archiviare nella cartella giusta, avvisare i colleghi, rispettare lo standard di nomenclatura: tutte cose che tutti sanno come fare, ma che di fretta e sotto pressione possono venire disattese o fatte a metà.

L'idea è togliere quel costo cognitivo automatizzando tutto ciò che è meccanico, e lasciare all'intelligenza umana solo le decisioni che richiedono davvero giudizio: quale tipo di pratica è questa? Chi deve seguirla?

Un principio guida che ha attraversato tutto lo sviluppo: **archiviare solo ciò che il tecnico approva esplicitamente**. I trigger automatici sono stati deliberatamente scartati in favore di gesti intenzionali — l'etichetta Gmail, la compilazione del form. Il sistema riduce la frizione ma non bypassa il giudizio umano.

### Roadmap

**v1.1 — Multi-utente, VTEnext e robustezza**
Aggiunta delle caselle Gmail di tutti i tecnici `@sigmapiu.it` a CONFIG.UTENTI. Integrazione VTEnext: configurazione webhook BPM verso l'endpoint `doPost()` già pronto, censimento commesse attive con campo Drive path, verifica modulo Progetti. Log errori nelle Bucoliche con notifica automatica all'amministratore. Script di sincronizzazione anagrafica Clienti_Siti ↔ VTEnext.

**v2.0 — Classificatore intelligente**
Agente AI (Claude API) che legge oggetto, corpo e allegati della mail e suggerisce automaticamente cliente, sito e tipo pratica. Il tecnico approva o corregge — non parte da zero. I dati ML già raccolti nelle Bucoliche (colonne 11-17) costituiscono il training set. Sotto l'85% di confidenza chiede conferma, sopra archivia direttamente.

**v2.1 — Guardiano delle scadenze**
Lettura delle date di scadenza dalle Bucoliche. Alert automatici 90 / 60 / 30 giorni prima della scadenza su Google Chat e Telegram con nome pratica e tecnico responsabile (AUA 15 anni, AIA 10 anni, reportAIA annuali).

**v3.0 — Knowledge base Sigma+**
Indicizzazione dell'archivio nell'Empireo. Possibilità di fare domande in linguaggio naturale: *"Quali prescrizioni AIA aveva Rossi Metalli nel 2022?"* Estrattore automatico di dati dai PDF (prescrizioni, limiti, scadenze) verso le Bucoliche.

**Beatrice**
Modulo economico per raccogliere dati utili per preventivi, fatture, pagamenti. Collegamento con le commesse archiviate da Virgilio. Dashboard di redditività per cliente e per tipo pratica, da integrare con VTEnext.

---

## Architettura tecnica

```
FORM VIRGILIO (HTML Web App — 4 step, dropdown dinamici da anagrafica)
  ↓  google.script.run.apriPraticaDaVirgilio(dati)
CARONTE (Apps Script doPost)
  ↓  crea cartella copiando Adamo
EMPIREO (Google Drive)  →  Cliente / Sito / Anno_TipoPratica + 00_autorizzazioni / 01_dati-ditta / 02_corrispondenza
  ↓  sposta allegati dal Limbo → 02_corrispondenza
  ↓  aggiorna righe gmail_staging → gmail_archiviato nelle Bucoliche
  ↓  notifica
GOOGLE CHAT (Markdown)  +  TELEGRAM (HTML + link cliccabili)
  ↓  registra
BUCOLICHE (Google Sheets — tab: bucoliche + Clienti_Siti + Team + TipiPratica)

TRIGGER GMAIL (ogni 5 min) → da-traghettare → Limbo → traghettate
```

### File del progetto Apps Script

| File | Contenuto |
|---|---|
| `caronte.gs` | CONFIG, doPost, caronteTraghetta, creaCartellaPratica, _spostaAllegatiDalLimbo, filtri allegati, helpers Gmail/Drive |
| `notifiche.gs` | avvisaTeam, avvisaTraghettamentoTeam, avvisaChat, avvisaTelegram, costruzione messaggi separati per canale |
| `bucoliche.gs` | registraSuBucoliche, aggiornaRigheAllegati, registraErrore, schema 17 colonne, _timestampLocale |
| `anagrafica.gs` | getAnagraficaVirgilio, aggiungiClienteSito, inizializzaAnagrafica, gestione tab Clienti_Siti / Team / TipiPratica |
| `webapp.gs` | doGet, _creaDataUriImmagine (logo Virgilio come data URI) |
| `test.gs` | caronteTest — verifica stato credenziali, Drive, Sheets, notifiche |
| `setup.gs` | caronteSetupTrigger, caronteSetupCredenziali, caronteSetupAnagrafica, generaToken, caronteStatoCredenziali |
| `virgilio.html` | Form a 4 step, dropdown dinamici, wizard UX, tema pergamena |

---

## Dipendenze tecniche

| Componente | Tecnologia | Note |
|---|---|---|
| Script di automazione | Google Apps Script | Account motore: `marco@sigmapiu.it` |
| Archivio documenti (Empireo) | Google Drive | Cartella radice ID configurato in CONFIG |
| Registro operazioni (Bucoliche) | Google Sheets | 17 colonne + 3 tab anagrafica |
| Template cartelle (Adamo) | Google Drive | Cartella copiata per ogni nuovo sito |
| Staging allegati (Limbo) | Google Drive | Cartella temporanea dentro l'Empireo |
| Notifiche team | Google Chat (webhook) + Telegram Bot | Messaggi separati con formattazione per canale |
| CRM | VTEnext (cloud) | Integrazione webhook prevista in v1.1 |
| Progetto cloud | Google Cloud | API abilitate: Gmail, Drive, Sheets, Chat |
| Autenticazione | OAuth2 con Domain-Wide Delegation | Per accesso caselle `@sigmapiu.it` |
| Form apertura pratica | HTML/JS Web App | Deployata come Apps Script Web App |
| Ambiente sviluppo / documentazione | Google Colab | Notebook con cosmologia, specifiche e log sviluppo |

---

*Progetto Virgilio — Sigma+ — Documentazione interna — versione 1.0 mono-utente*
