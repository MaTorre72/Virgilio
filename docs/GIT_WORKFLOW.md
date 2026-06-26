# Workflow Git per Virgilio

Questo repository usa Git per separare versione stabile, sviluppo sperimentale e documentazione.

## Rami principali

| Ramo | Uso |
|---|---|
| `main` | Versione stabile o fotografia consolidata |
| `codex/v1.1-development` | Sviluppo tecnico v1.1 |
| `docs/roadmap-architettura-modulare` | Documentazione roadmap; puo' essere rinominato `roadmap` |

## Regola pratica

Non moltiplicare branch se non serve. Per la fase attuale:

- documentazione: lavorare su `docs/roadmap-architettura-modulare`;
- sviluppo tecnico: lavorare su `codex/v1.1-development`;
- prototipi brevi: branch dedicata solo se il rischio e' reale;
- branch superate: eliminare solo dopo conferma e dopo avere consolidato documentazione/codice utile.

## Versioni

| Versione | Significato |
|---|---|
| `v1.0` | MVP Google Workspace mono-utente funzionante |
| `v1.1` | Evoluzione sperimentale verso Caronte Locale multi-casella |

## Procedura per aggiornare documentazione

```powershell
git switch docs/roadmap-architettura-modulare
git pull
git status
```

Modificare i file `.md`, poi:

```powershell
git diff
git add README.md docs
git commit -m "docs: aggiorna roadmap Caronte locale"
git push
```

## Procedura per sviluppo tecnico

```powershell
git switch codex/v1.1-development
git pull
git status
```

Poi lavorare su una funzione alla volta. Prima del commit:

```powershell
git diff
python -m pytest local_connector
git status
```

Commit:

```powershell
git add .
git commit -m "feat: descrizione sintetica"
git push
```

## Regole pratiche

- Non inserire credenziali reali nel repository.
- Non committare `.env`.
- Tenere segreti in variabili ambiente, PropertiesService o strumenti equivalenti.
- Non modificare il tag `v1.0`.
- Fare commit piccoli e leggibili.
- Non usare Codex per cancellare branch senza conferma esplicita.
- Non fare merge su `main` finche' v1.1 non e' collaudata.
