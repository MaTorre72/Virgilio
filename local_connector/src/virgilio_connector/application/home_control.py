"""Application controller for the primary actions on Caronte Home."""

from __future__ import annotations

from pathlib import Path

from .operation_runner import ManagedOperationRunner, RunnerEvent


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
        self.set_interval_seconds(interval_seconds)

    @property
    def state(self) -> str:
        return self._runner.state

    def check_now(self) -> bool:
        return self._runner.start(self._arguments(max_cycles=1))

    def start(self) -> bool:
        return self._runner.start(self._arguments(max_cycles=None))

    def pause(self) -> bool:
        return self._runner.stop()

    def close(self) -> None:
        self._runner.close()

    def set_interval_seconds(self, value: int) -> None:
        if not 60 <= int(value) <= 86_400:
            raise ValueError("interval_seconds must be between 60 and 86400")
        self._interval_seconds = int(value)

    def drain_events(self) -> list[RunnerEvent]:
        return self._runner.drain_events()

    def _arguments(self, *, max_cycles: int | None) -> list[str]:
        args = [
            "watch",
            "--config",
            str(self._config_path),
            "--human",
            "--interval-seconds",
            str(self._interval_seconds),
        ]
        if max_cycles is not None:
            args.extend(("--max-cycles", str(max_cycles)))
        return args
