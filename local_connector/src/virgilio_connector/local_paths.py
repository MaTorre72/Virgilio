"""Configurable local data layout for the read-only quarantine phase."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .application_paths import default_application_paths


@dataclass(frozen=True, slots=True)
class LocalDataPaths:
    root: Path = field(default_factory=lambda: default_application_paths().data_dir)

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
