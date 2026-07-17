"""Minimal user-facing Home for Caronte."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo

from ..application.home_control import HomeFeedback
from ..application.home_status import HomeStatus, HomeStatusService


ROME = ZoneInfo("Europe/Rome")


def format_home_time(value: datetime | None) -> str:
    if value is None:
        return "Non ancora"
    return value.astimezone(ROME).strftime("%d/%m/%Y %H:%M")


class HomeView:
    """Render only the essential status and primary user actions."""

    def __init__(
        self,
        parent: Any,
        status_service: HomeStatusService,
        *,
        ttk_module: Any,
        check_now: Callable[[], None] = lambda: None,
        start: Callable[[], None] = lambda: None,
        pause: Callable[[], None] = lambda: None,
        open_configuration: Callable[[], None] = lambda: None,
        open_activity: Callable[[], None] = lambda: None,
        open_settings: Callable[[], None] = lambda: None,
        open_bucoliche_startup: Callable[[], None] = lambda: None,
    ) -> None:
        self.frame = ttk_module.Frame(parent)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.status = status_service.get_status()
        self._ttk = ttk_module
        self._render(ttk_module, check_now, start, pause)
        ttk_module.Button(
            self.frame, text="Caselle", command=open_configuration
        ).grid(row=7, column=0, sticky="w", pady=(16, 0))
        ttk_module.Button(
            self.frame, text="Attivita e problemi", command=open_activity
        ).grid(row=7, column=1, sticky="w", pady=(16, 0))
        ttk_module.Button(
            self.frame, text="Impostazioni", command=open_settings
        ).grid(row=7, column=2, sticky="w", pady=(16, 0))
        ttk_module.Button(
            self.frame, text="Bucoliche e avvio", command=open_bucoliche_startup
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _render(
        self,
        ttk_module: Any,
        check_now: Callable[[], None],
        start: Callable[[], None],
        pause: Callable[[], None],
    ) -> None:
        values = (
            ("Home", None),
            ("Stato generale", self.status.state),
            ("Caselle attive", str(self.status.active_accounts)),
            ("Ultimo controllo", format_home_time(self.status.last_check)),
        )
        for row, (label, value) in enumerate(values):
            text = label if value is None else f"{label}: {value}"
            widget = ttk_module.Label(self.frame, text=text)
            widget.grid(
                row=row, column=0, columnspan=3, sticky="w", pady=(0, 8)
            )
            if label == "Stato generale":
                self.state_label = widget
            elif label == "Ultimo controllo":
                self.last_check_label = widget
        for column, (text, command) in enumerate((
            ("Controlla ora", check_now),
            ("Avvia", start),
            ("Pausa", pause),
        )):
            ttk_module.Button(self.frame, text=text, command=command).grid(
                row=len(values), column=column, sticky="w", padx=(0, 8)
            )
        self.feedback_label = ttk_module.Label(self.frame, text="Pronto per il prossimo controllo.")
        self.feedback_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(12, 0))
        self.activity_label = ttk_module.Label(self.frame, text="")
        self.activity_label.grid(row=6, column=0, columnspan=3, sticky="w", pady=(4, 0))

    def apply_feedback(self, feedback: HomeFeedback, *, activity_count: int | None = None) -> None:
        self.status = HomeStatus(
            feedback.state,
            self.status.active_accounts,
            feedback.last_check if feedback.last_check is not None else self.status.last_check,
        )
        self.state_label.configure(text=f"Stato generale: {self.status.state}")
        self.last_check_label.configure(text=f"Ultimo controllo: {format_home_time(self.status.last_check)}")
        self.feedback_label.configure(text=feedback.message)
        if activity_count is not None:
            self.activity_label.configure(text=f"Attivita aggiornate: {activity_count}")


class StaticHomeStatusService:
    """Small deterministic service for tests and presentation composition."""

    def __init__(self, status: HomeStatus) -> None:
        self._status = status

    def get_status(self) -> HomeStatus:
        return self._status
