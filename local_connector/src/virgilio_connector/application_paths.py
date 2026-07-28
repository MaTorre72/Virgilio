"""Windows application paths shared by every Caronte presentation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ApplicationPaths:
    """Authoritative configuration and data roots, independent from the cwd."""

    config_dir: Path
    data_dir: Path

    def __post_init__(self) -> None:
        if not self.config_dir.is_absolute() or not self.data_dir.is_absolute():
            raise ValueError("application configuration and data directories must be absolute")

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> "ApplicationPaths":
        values = os.environ if environ is None else environ
        user_home = Path(values.get("USERPROFILE") or Path.home())
        roaming_root = Path(values.get("APPDATA") or user_home / "AppData" / "Roaming")
        local_root = Path(values.get("LOCALAPPDATA") or user_home / "AppData" / "Local")
        return cls(
            config_dir=Path(values.get("VIRGILIO_CONFIG_DIR") or roaming_root / "Caronte"),
            data_dir=Path(values.get("VIRGILIO_LOCAL_DATA_DIR") or local_root / "Caronte"),
        )

    @property
    def configuration_file(self) -> Path:
        return self.config_dir / "config.yaml"

    def create(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


def default_application_paths() -> ApplicationPaths:
    """Resolve paths at call time so tests and launchers can inject environment roots."""

    return ApplicationPaths.from_environment()
