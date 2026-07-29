"""Application controller for the primary actions on Caronte Home."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from zoneinfo import ZoneInfo

from .operation_runner import ManagedOperationRunner, RunnerEvent


ROME = ZoneInfo("Europe/Rome")


@dataclass(frozen=True, slots=True)
class HomeFeedback:
    state: str
    message: str
    last_check: datetime | None = None
    refresh_activity: bool = False
    activity: str = ""


class HomeRunController:
    """Translate Home intentions into one owned background worker."""

    def __init__(
        self,
        config_path: Path,
        runner: ManagedOperationRunner,
        *,
        interval_seconds: int = 300,
    ) -> None:
        self._config_path = Path(config_path)
        self._runner = runner
        self._feedback: Queue[HomeFeedback] = Queue()
        self._operation: str | None = None
        self.set_interval_seconds(interval_seconds)

    @property
    def state(self) -> str:
        return self._runner.state

    def check_now(self) -> bool:
        return self._begin("check", self._arguments(max_cycles=1))

    def start(self) -> bool:
        return self._begin("continuous", self._arguments(max_cycles=None))

    def pause(self) -> bool:
        accepted = self._runner.stop()
        if accepted:
            self._feedback.put(HomeFeedback(
                "In pausa", "Pausa richiesta. Attendi la conclusione del controllo in corso.",
                activity="Pausa richiesta",
            ))
        return accepted

    def close(self) -> None:
        self._runner.close()

    def set_interval_seconds(self, value: int) -> None:
        if not 60 <= int(value) <= 86_400:
            raise ValueError("interval_seconds must be between 60 and 86400")
        self._interval_seconds = int(value)

    def drain_events(self) -> list[RunnerEvent]:
        return self._runner.drain_events()

    def drain_feedback(self) -> list[HomeFeedback]:
        feedback: list[HomeFeedback] = []
        while True:
            try:
                feedback.append(self._feedback.get_nowait())
            except Empty:
                break
        for event in self._runner.drain_events():
            feedback.append(self._translate(event))
        return feedback

    def _begin(self, operation: str, args: list[str]) -> bool:
        accepted = self._runner.start(args)
        if accepted:
            self._operation = operation
            message = (
                "Controllo richiesto. Attendi il risultato."
                if operation == "check"
                else "Avvio richiesto. Caronte iniziera` a controllare le caselle."
            )
            self._feedback.put(HomeFeedback(
                "Controllo in corso", message,
                activity=("Controllo richiesto" if operation == "check" else "Controllo automatico avviato"),
            ))
        return accepted

    def _translate(self, event: RunnerEvent) -> HomeFeedback:
        if event.kind == "progress":
            if event.state == "error":
                return HomeFeedback(
                    "Richiede attenzione",
                    "Non riesco a completare il controllo. Riprova; se il problema continua, chiedi assistenza.",
                    activity="Controllo richiede attenzione",
                )
            if event.phase == "In attesa del Registro":
                return HomeFeedback(
                    "Controllo in corso", "In attesa del Registro. Attendi oppure riprova tra poco.",
                    activity=event.phase,
                )
            counts = _format_counts(event)
            return HomeFeedback(
                "Controllo in corso", f"{event.phase}.{counts}", activity=event.phase,
            )
        if event.kind == "started":
            message = (
                "Controllo delle caselle in corso."
                if self._operation == "check"
                else "Caronte e` attivo e controllera` periodicamente le caselle."
            )
            return HomeFeedback("Controllo in corso", message, activity="Controllo in corso")
        if event.kind == "rejected":
            return HomeFeedback(
                "Controllo in corso" if self._runner.running else "In pausa",
                "Richiesta non avviata: un controllo e` gia` in corso."
                if self._runner.running
                else "Richiesta non eseguita: Caronte e` gia` in pausa.",
                activity="Richiesta non eseguita",
            )
        if event.kind == "stopped":
            self._operation = None
            return HomeFeedback("In pausa", "Caronte e` in pausa.", activity="Controllo automatico in pausa")
        if event.kind == "completed" and event.returncode == 0:
            operation = self._operation
            self._operation = None
            if operation == "check":
                return HomeFeedback(
                    "Pronto",
                    "Controllo completato. Apri Attivita e problemi per vedere i risultati.",
                    datetime.now(ROME),
                    True,
                    "Controllo completato",
                )
            return HomeFeedback(
                "In pausa", "Il controllo automatico si e` concluso.",
                refresh_activity=True, activity="Controllo automatico concluso",
            )
        self._operation = None
        return HomeFeedback(
            "Richiede attenzione",
            "Controllo non completato. Riprova; se il problema continua, chiedi assistenza.",
            refresh_activity=True,
            activity="Controllo non completato",
        )

    def _arguments(self, *, max_cycles: int | None) -> list[str]:
        args = [
            "watch",
            "--config",
            str(self._config_path),
            "--human",
            "--progress-events",
            "--interval-seconds",
            str(self._interval_seconds),
        ]
        if max_cycles is not None:
            args.extend(("--max-cycles", str(max_cycles)))
            args.extend((
                "--completion-followup-seconds", "0",
                "--completion-poll-seconds", "30",
            ))
        return args


def _format_counts(event: RunnerEvent) -> str:
    values = (
        ("Documenti trovati", event.found),
        ("elaborati", event.processed),
        ("rimanenti", event.remaining),
    )
    known = [f"{label}: {value}" for label, value in values if value is not None]
    return " " + "; ".join(known) + "." if known else ""
