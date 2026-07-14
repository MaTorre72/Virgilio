"""User-facing operational snapshot for the local Caronte home."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .gui_runner import RunnerEvent


ROME = ZoneInfo("Europe/Rome")


@dataclass(frozen=True, slots=True)
class HomeSnapshot:
    state: str = "Configurazione da completare"
    active_accounts: int = 0
    checks: int = 0
    completed: int = 0
    problems: int = 0
    last_check: datetime | None = None
    next_check: datetime | None = None
    problem: str = "Seleziona o crea una configurazione locale."

    def with_accounts(self, active: int, *, problem: str = "") -> "HomeSnapshot":
        return replace(
            self,
            active_accounts=active,
            state="Pronto" if active else "Nessuna casella attiva",
            problem=problem or ("" if active else "Attiva almeno una casella mail."),
        )

    def apply(self, event: RunnerEvent, *, now: datetime,
              interval_seconds: int = 300) -> "HomeSnapshot":
        timestamp = now.astimezone(ROME)
        if event.state in {"running", "stopping"}:
            labels = {"running": "Controllo in corso", "stopping": "Arresto in corso"}
            return replace(self, state=labels[event.state], problem="")
        if event.state == "error" or (event.returncode not in {None, 0}):
            return replace(self, state="Richiede attenzione", checks=self.checks + 1,
                           problems=self.problems + 1, last_check=timestamp,
                           next_check=None, problem="Il controllo non e` riuscito. Apri il report.")
        if event.kind in {"completed", "stopped"}:
            return replace(self, state="Pronto", checks=self.checks + 1,
                           completed=self.completed + (event.kind == "completed"),
                           last_check=timestamp,
                           next_check=timestamp + timedelta(seconds=interval_seconds), problem="")
        return self


def format_home_time(value: datetime | None) -> str:
    return value.astimezone(ROME).strftime("%d/%m/%Y %H:%M") if value else "Non ancora"
