"""Shared use cases for Caronte's ordinary settings."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from ..multi_account import MultiAccountConfigError
from .configuration import ConfigurationService, UserPreferences


class SettingsValidationError(ValueError):
    """Raised when a user-facing setting is invalid."""


class StartupPreferenceAdapter(Protocol):
    def set_enabled(self, enabled: bool) -> None: ...


class DisabledStartupAdapter:
    """Safe adapter for environments where sign-in integration is unavailable."""

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            raise SettingsValidationError(
                "L'avvio automatico non e` disponibile in questo ambiente."
            )


@dataclass(frozen=True, slots=True)
class SettingsSnapshot:
    limbo: Path
    interval_minutes: int
    start_with_windows: bool
    minimize_on_close: bool


class SettingsService:
    """Read and save ordinary settings through their authoritative adapters."""

    def __init__(
        self,
        configuration: ConfigurationService,
        startup: StartupPreferenceAdapter,
    ) -> None:
        self.configuration = configuration
        self.startup = startup

    def load(self) -> SettingsSnapshot:
        model = self.configuration.load()
        return SettingsSnapshot(
            limbo=model.storage.staging_dir,
            interval_minutes=model.preferences.interval_seconds // 60,
            start_with_windows=model.preferences.start_with_windows,
            minimize_on_close=model.preferences.minimize_on_close,
        )

    def save(
        self,
        *,
        limbo: str,
        interval_minutes: str,
        start_with_windows: bool,
        minimize_on_close: bool,
    ) -> SettingsSnapshot:
        folder = Path(limbo.strip()).expanduser()
        if not limbo.strip() or not folder.is_absolute() or not folder.is_dir():
            raise SettingsValidationError("Scegli una cartella Limbo valida.")
        try:
            minutes = int(interval_minutes.strip())
        except ValueError as exc:
            raise SettingsValidationError(
                "Indica ogni quanti minuti effettuare il controllo."
            ) from exc
        if not 1 <= minutes <= 1440:
            raise SettingsValidationError(
                "L'intervallo deve essere compreso tra 1 e 1440 minuti."
            )
        model = self.configuration.load()
        preferences = UserPreferences(
            interval_seconds=minutes * 60,
            start_with_windows=start_with_windows,
            minimize_on_close=minimize_on_close,
        )
        try:
            preferences.validate()
        except MultiAccountConfigError as exc:
            raise SettingsValidationError(str(exc)) from exc
        self.startup.set_enabled(start_with_windows)
        try:
            self.configuration.save(
                replace(
                    model,
                    storage=replace(model.storage, staging_dir=folder),
                    preferences=preferences,
                )
            )
        except Exception:
            self.startup.set_enabled(model.preferences.start_with_windows)
            raise
        return self.load()
