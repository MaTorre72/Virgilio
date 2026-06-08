# Workflow Git per Virgilio/Caronte

Questo repository usa Git per separare la versione stabile dallo sviluppo.

## Rami

- `main`: versione stabile.
- `codex/v1.1-development`: sviluppo della prossima versione.

## Versioni

- `v1.0`: fotografia della versione funzionante mono-utente.
- `v1.1`: prossima versione, dedicata a multi-mailbox, Gmail bridge, sicurezza Limbo e integrazioni successive.

## Procedura ordinaria

1. Lavorare sul ramo di sviluppo:

   ```powershell
   git switch codex/v1.1-development
   ```

2. Controllare le modifiche:

   ```powershell
   git status
   git diff
   ```

3. Salvare un avanzamento:

   ```powershell
   git add .
   git commit -m "Descrizione breve della modifica"
   ```

4. Quando la versione e pronta, rientrare su `main` e integrare:

   ```powershell
   git switch main
   git merge codex/v1.1-development
   git tag v1.1
   ```

## Regole pratiche

- Non inserire credenziali reali nel repository.
- Tenere i segreti in Apps Script Properties, Secret Manager o variabili ambiente.
- Non modificare il tag `v1.0`: serve come punto di ripristino.
- Prima di ogni modifica importante, creare un commit piccolo e leggibile.
- I file in `_old/`, PDF, DOCX e notebook generati restano locali salvo decisione esplicita.
