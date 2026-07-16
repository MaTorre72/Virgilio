"""User-facing view for ordinary Caronte settings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..application.settings import SettingsService, SettingsValidationError


@dataclass(frozen=True, slots=True)
class SaveResult:
    is_valid: bool
    message: str = ""


class SettingsView:
    def __init__(
        self,
        parent: Any,
        service: SettingsService,
        *,
        ttk_module: Any,
        go_home: Callable[[], None],
        on_saved: Callable[[int, bool], None],
    ) -> None:
        self.service = service
        self._on_saved = on_saved
        self.frame = ttk_module.Frame(parent)
        self.frame.grid(row=0, column=0, sticky="nsew")
        current = service.load()
        self._start_with_windows = current.start_with_windows
        self._minimize_on_close = current.minimize_on_close

        ttk_module.Label(self.frame, text="Impostazioni").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        ttk_module.Label(self.frame, text="Cartella Limbo").grid(
            row=1, column=0, sticky="w"
        )
        self.limbo_entry = ttk_module.Entry(self.frame)
        self.limbo_entry.grid(row=1, column=1, sticky="ew")
        self.limbo_entry.insert(0, str(current.limbo))

        ttk_module.Label(self.frame, text="Controlla ogni quanti minuti").grid(
            row=2, column=0, sticky="w"
        )
        self.interval_entry = ttk_module.Entry(self.frame)
        self.interval_entry.grid(row=2, column=1, sticky="ew")
        self.interval_entry.insert(0, str(current.interval_minutes))

        self.startup_control = ttk_module.Checkbutton(
            self.frame,
            text="Avvia Caronte quando accedo a Windows",
            command=self.toggle_start_with_windows,
        )
        self.startup_control.grid(row=3, column=0, columnspan=2, sticky="w")
        self.close_control = ttk_module.Checkbutton(
            self.frame,
            text="Alla chiusura, riduci Caronte a icona",
            command=self.toggle_minimize_on_close,
        )
        self.close_control.grid(row=4, column=0, columnspan=2, sticky="w")
        self._sync_controls()

        self.message = ttk_module.Label(self.frame, text="")
        self.message.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk_module.Button(self.frame, text="Salva", command=self.save).grid(
            row=6, column=0, sticky="w", pady=(12, 0)
        )
        ttk_module.Button(self.frame, text="Torna alla Home", command=go_home).grid(
            row=6, column=1, sticky="w", pady=(12, 0)
        )

    def toggle_start_with_windows(self) -> None:
        self._start_with_windows = not self._start_with_windows
        self._sync_controls()

    def toggle_minimize_on_close(self) -> None:
        self._minimize_on_close = not self._minimize_on_close
        self._sync_controls()

    def save(self) -> SaveResult:
        try:
            saved = self.service.save(
                limbo=self.limbo_entry.get(),
                interval_minutes=self.interval_entry.get(),
                start_with_windows=self._start_with_windows,
                minimize_on_close=self._minimize_on_close,
            )
        except SettingsValidationError as exc:
            self.message.configure(text=str(exc))
            return SaveResult(False, str(exc))
        self._on_saved(saved.interval_minutes * 60, saved.minimize_on_close)
        message = "Impostazioni salvate."
        self.message.configure(text=message)
        return SaveResult(True, message)

    def _sync_controls(self) -> None:
        self.startup_control.state(
            ("selected",) if self._start_with_windows else ("!selected",)
        )
        self.close_control.state(
            ("selected",) if self._minimize_on_close else ("!selected",)
        )
