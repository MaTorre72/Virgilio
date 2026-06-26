# Struttura del repository

Questo documento descrive la struttura logica del repository Virgilio.

## Radice repository

I file Apps Script restano nella radice per mantenere semplice il collegamento con il progetto Google.

| File | Ruolo |
|---|---|
| `caronte.gs` | Motore operativo v1.0 Google / funzioni Apps Script |
| `bucoliche.gs` | Registro Google Sheets |
| `notifiche.gs` | Google Chat e Telegram |
| `anagrafiche.gs` | Clienti, siti, team, tipi pratica |
| `setup.gs` | Trigger e configurazione PropertiesService |
| `test.gs` | Test manuali Apps Script |
| `webapp.gs` | Endpoint HTML service |
| `virgilio.html` | Interfaccia form |

Con la v1.1, questi file vanno considerati **adapter Google** o prototipo v1.0, non il nucleo definitivo del multi-casella.

## Local connector / Caronte Locale

Il codice del connettore locale vive in:

```text
local_connector/
```

Ruolo aggiornato:

- lettura IMAP;
- gestione multi-account;
- quarantena locale;
- scanner;
- manifest;
- SQLite;
- staging/storage adapter;
- futuro ack IMAP locale.

Nel linguaggio architetturale, questo componente evolve verso **Caronte Locale**.

## Documentazione

| File | Ruolo |
|---|---|
| `README.md` | Sintesi del progetto e stato corrente |
| `docs/01_ARCHITETTURA_E_ROADMAP.md` | Architettura e roadmap aggiornata |
| `docs/02_DECISIONI_E_RISCHI.md` | Decisioni architetturali e rischi |
| `docs/03_SICUREZZA_E_TEST.md` | Checklist sicurezza e test |
| `docs/04_RICOGNIZIONE_E_CONNETTORI.md` | Ricognizione e confronto connettori |
| `docs/GIT_WORKFLOW.md` | Workflow Git |
| `docs/REPO_STRUCTURE.md` | Questa mappa |

Eventuali documenti storici o duplicati possono andare in:

```text
docs/archive/
```

Non cancellare documenti storici senza conferma.

## Asset

- `Virgilio.png`, `VirgilioBN.png`: asset correnti.
- `Virgilio_1.0.png`, `VirgilioBN_1.0.png`: asset congelati per v1.0.
- `*.svg`: diagrammi e materiali visuali sorgente.

## Esclusi da Git

La configurazione `.gitignore` deve escludere:

- credenziali e token locali;
- `.env`;
- `_old/` e archivi ZIP storici;
- PDF, DOCX e notebook generati;
- cache Python;
- ambienti virtuali;
- configurazioni locali di editor;
- dati locali del connettore;
- allegati scaricati;
- database SQLite locali reali, salvo esempi fittizi.

Questi file restano sul disco, ma non devono entrare nella storia Git.

## Principio di ordine

La struttura deve restare semplice:

```text
root = Apps Script / prototipo Google
local_connector = Caronte Locale
docs = decisioni e roadmap
```

Evitare nuove cartelle o branch se non servono a ridurre rischio reale.
