"""Minimal, independent shell for the Caronte user application."""

from __future__ import annotations

from pathlib import Path
from tkinter import ttk
from typing import Any

from ..application.account_connection import (
    AccountConnectionRequest,
    ReadonlyAccountConnectionService,
)
from ..application.configuration import ConfigurationService
from ..application.account_management import AccountManagementService
from ..application.windows_credentials import create_account_credential_service
from ..application_paths import default_application_paths
from .navigation import UserRoute, initial_route
from .wizard import AccountForm, FirstRunController


WINDOW_TITLE = "Caronte"
USER_VIEWS = ("Primo avvio", "Home")

_VIEW_CONTENT = {
    UserRoute.FIRST_RUN: (
        "Primo avvio",
        "Configuriamo insieme gli elementi necessari per iniziare.",
    ),
    UserRoute.HOME: (
        "Home",
        "Caronte e` pronto.",
    ),
}


class UserAppShell:
    """Own the root window and route to the first user-facing screen."""

    def __init__(
        self,
        root: Any,
        configuration: ConfigurationService,
        *,
        ttk_module: Any = ttk,
        readonly_test: Any | None = None,
        account_service: AccountManagementService | None = None,
    ) -> None:
        self.root = root
        self._ttk = ttk_module
        self._readonly_test = readonly_test
        self._account_service = account_service
        self.route = initial_route(configuration)
        self.root.title(WINDOW_TITLE)
        self.root.minsize(720, 480)
        self.current_frame: Any | None = None
        self.first_run: FirstRunController | None = None
        self._render()

    def _render(self) -> None:
        frame = self._ttk.Frame(self.root, padding=32)
        frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = frame
        if self.route is UserRoute.FIRST_RUN:
            self.first_run = FirstRunController(
                frame, ttk_module=self._ttk, readonly_test=self._readonly_test,
                account_service=self._account_service,
            )
            return
        heading, description = _VIEW_CONTENT[self.route]
        self._ttk.Label(frame, text=heading).grid(row=0, column=0, sticky="w")
        self._ttk.Label(frame, text=description).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(12, 0),
        )


def launch_user_app(*, config_path: Path | None = None) -> int:
    """Create and run the Caronte window."""

    from tkinter import Tk

    paths = default_application_paths()
    configuration = ConfigurationService.for_file(config_path or paths.configuration_file)
    account_service = AccountManagementService(
        configuration, create_account_credential_service()
    )
    connection = ReadonlyAccountConnectionService(paths.data_dir / "connection-check")
    root = Tk()
    UserAppShell(
        root,
        configuration,
        readonly_test=lambda form: connection.check(_connection_request(form)),
        account_service=account_service,
    )
    root.mainloop()
    return 0


def _connection_request(form: AccountForm) -> AccountConnectionRequest:
    return AccountConnectionRequest(
        email=form.email,
        password=form.password,
        host=form.host,
        port=form.port,
    )
