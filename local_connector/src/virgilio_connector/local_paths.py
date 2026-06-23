"""Configurable local data layout for the read-only quarantine phase."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LocalDataPaths:
    root: Path = Path(".local_data")

    @property
    def quarantine(self) -> Path:
        return self.root / "quarantine"

    @property
    def incoming(self) -> Path:
        return self.quarantine / "incoming"

    @property
    def rejected(self) -> Path:
        return self.quarantine / "rejected"

    @property
    def ready(self) -> Path:
        return self.quarantine / "ready"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def state_db(self) -> Path:
        return self.root / "state.db"

    def create(self) -> None:
        for path in (self.incoming, self.rejected, self.ready, self.logs):
            path.mkdir(parents=True, exist_ok=True)
