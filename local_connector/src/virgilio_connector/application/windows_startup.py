"""Windows sign-in adapter for Caronte."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Any

from .settings import SettingsValidationError


class WindowsStartupAdapter:
    """Manage the current user's Caronte sign-in command in the Windows registry."""

    KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    VALUE_NAME = "Caronte"

    def __init__(self, config_path: Path, *, registry: Any | None = None) -> None:
        if registry is None:
            try:
                import winreg as registry
            except ImportError as exc:
                raise SettingsValidationError(
                    "L'avvio automatico e` disponibile solo su Windows."
                ) from exc
        self._registry = registry
        command = [sys.executable]
        if not getattr(sys, "frozen", False):
            command.extend(("-m", "virgilio_connector"))
        command.extend(("user-gui", "--config", str(Path(config_path).resolve())))
        self._command = subprocess.list2cmdline(command)

    def set_enabled(self, enabled: bool) -> None:
        try:
            with self._registry.CreateKeyEx(
                self._registry.HKEY_CURRENT_USER,
                self.KEY,
                0,
                self._registry.KEY_SET_VALUE,
            ) as key:
                if enabled:
                    self._registry.SetValueEx(
                        key, self.VALUE_NAME, 0, self._registry.REG_SZ, self._command
                    )
                else:
                    try:
                        self._registry.DeleteValue(key, self.VALUE_NAME)
                    except FileNotFoundError:
                        pass
        except OSError as exc:
            raise SettingsValidationError(
                "Non e` stato possibile aggiornare l'avvio automatico."
            ) from exc


class WindowsAutomaticControlAdapter:
    """Register the frozen worker for the current user at Windows sign-in."""

    KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    VALUE_NAME = "Caronte - controllo automatico"

    def __init__(
        self,
        config_path: Path,
        interval_seconds: int,
        *,
        registry: Any | None = None,
        executable: Path | None = None,
        frozen: bool | None = None,
    ) -> None:
        if registry is None:
            try:
                import winreg as registry
            except ImportError as exc:
                raise SettingsValidationError(
                    "Il controllo automatico e` disponibile solo su Windows."
                ) from exc
        self._registry = registry
        is_frozen = getattr(sys, "frozen", False) if frozen is None else frozen
        command = [str(executable or sys.executable)]
        if not is_frozen:
            command.extend(("-m", "virgilio_connector"))
        command.extend(
            (
                "watch",
                "--config",
                str(Path(config_path).resolve()),
                "--human",
                "--interval-seconds",
                str(interval_seconds),
            )
        )
        self.command = subprocess.list2cmdline(command)

    def is_installed(self) -> bool:
        try:
            with self._registry.OpenKey(
                self._registry.HKEY_CURRENT_USER,
                self.KEY,
                0,
                self._registry.KEY_QUERY_VALUE,
            ) as key:
                value, _ = self._registry.QueryValueEx(key, self.VALUE_NAME)
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise SettingsValidationError(
                "Non e` stato possibile leggere il controllo automatico."
            ) from exc
        return value == self.command

    def install(self) -> None:
        try:
            with self._registry.CreateKeyEx(
                self._registry.HKEY_CURRENT_USER,
                self.KEY,
                0,
                self._registry.KEY_SET_VALUE,
            ) as key:
                self._registry.SetValueEx(
                    key,
                    self.VALUE_NAME,
                    0,
                    self._registry.REG_SZ,
                    self.command,
                )
        except OSError as exc:
            raise SettingsValidationError(
                "Non e` stato possibile attivare il controllo automatico."
            ) from exc

    def remove(self) -> None:
        try:
            with self._registry.OpenKey(
                self._registry.HKEY_CURRENT_USER,
                self.KEY,
                0,
                self._registry.KEY_SET_VALUE,
            ) as key:
                try:
                    self._registry.DeleteValue(key, self.VALUE_NAME)
                except FileNotFoundError:
                    pass
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise SettingsValidationError(
                "Non e` stato possibile disattivare il controllo automatico."
            ) from exc
