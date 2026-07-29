# Runbook

Installazione, dipendenze, comandi, test, build e procedure Apps Script sono in
[tecnica/INSTALLAZIONE_E_COMANDI.md](tecnica/INSTALLAZIONE_E_COMANDI.md).

Il percorso unico da clone pulito resta:

```powershell
git clone <URL-REPOSITORY> Virgilio
cd Virgilio
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/bootstrap_local_connector.ps1
local_connector\.venv\Scripts\python.exe -m virgilio_connector --help
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/smoke_local_connector.ps1
```

Questo percorso resta disponibile per compatibilita` con regole, link e
automazioni esistenti.
