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
