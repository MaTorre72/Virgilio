"""Minimal, independent shell for the Caronte user application."""

from __future__ import annotations

from pathlib import Path
from tkinter import ttk
from typing import Any

from ..application.account_connection import (
    AccountConnectionRequest,
    ReadonlyAccountConnectionService,
)
from ..application.account_management import AccountManagementService
from ..application.configuration import ConfigurationService
from ..application.home_status import AccountHomeStatusService, HomeStatus, HomeStatusService
from ..application.home_control import HomeRunController
from ..application.operation_runner import ManagedOperationRunner
from ..application.windows_credentials import create_account_credential_service
from ..application_paths import default_application_paths
from .home import HomeView, StaticHomeStatusService
from .navigation import UserRoute, initial_route
from .wizard import AccountForm, FirstRunController


WINDOW_TITLE = "Caronte"
USER_VIEWS = ("Primo avvio", "Home")

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
        home_status: HomeStatusService | None = None,
        home_control: HomeRunController | None = None,
    ) -> None:
        self.root = root
        self._ttk = ttk_module
        self._readonly_test = readonly_test
        self._account_service = account_service
        self._home_control = home_control or HomeRunController(
            configuration.store.source, ManagedOperationRunner()
        )
        self.route = initial_route(configuration)
        self.root.title(WINDOW_TITLE)
        self.root.minsize(720, 480)
        self.current_frame: Any | None = None
        self.first_run: FirstRunController | None = None
        self.home: HomeView | None = None
        self._home_status = home_status or (
            AccountHomeStatusService(account_service)
            if account_service is not None
            else StaticHomeStatusService(HomeStatus("Pronto", 0))
        )
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
        self.home = HomeView(
            frame,
            self._home_status,
            ttk_module=self._ttk,
            check_now=self._home_control.check_now,
            start=self._home_control.start,
            pause=self._home_control.pause,
        )
        if hasattr(self.root, "protocol"):
            self.root.protocol("WM_DELETE_WINDOW", self.close)

    def close(self) -> None:
        """Stop the owned worker before closing the window."""

        self._home_control.close()
        self.root.destroy()


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
