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
from ..application.activity import ActivityService
from ..application.configuration import ConfigurationService
from ..application.home_status import AccountHomeStatusService, HomeStatus, HomeStatusService
from ..application.home_control import HomeRunController
from ..application.operation_runner import ManagedOperationRunner
from ..application.windows_credentials import create_account_credential_service
from ..application_paths import default_application_paths
from .home import HomeView, StaticHomeStatusService
from .activity import ActivitySource, ActivityView, EmptyActivitySource
from .navigation import UserRoute, initial_route
from .wizard import AccountForm, FirstRunController


WINDOW_TITLE = "Caronte"
USER_VIEWS = ("Primo avvio", "Home", "Attivita e problemi")

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
        activity_service: ActivitySource | None = None,
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
        self.activity: ActivityView | None = None
        self._activity_service = activity_service or EmptyActivitySource()
        self._home_status = home_status or (
            AccountHomeStatusService(account_service)
            if account_service is not None
            else StaticHomeStatusService(HomeStatus("Pronto", 0))
        )
        self._render()
        if hasattr(self.root, "protocol"):
            self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _render(self, *, open_existing: bool = False) -> None:
        if self.current_frame is not None:
            self.current_frame.destroy()
        frame = self._ttk.Frame(self.root, padding=32)
        frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = frame
        controls = self._ttk.Frame(frame)
        controls.grid(row=0, column=0, sticky="e")
        self._ttk.Button(
            controls, text="Riduci a icona", command=self.minimize
        ).grid(row=0, column=0, padx=(0, 8))
        self._ttk.Button(controls, text="Chiudi", command=self.close).grid(
            row=0, column=1
        )
        content = self._ttk.Frame(frame)
        content.grid(row=1, column=0, sticky="nsew")
        if self.route is UserRoute.FIRST_RUN:
            self.first_run = FirstRunController(
                content, ttk_module=self._ttk, readonly_test=self._readonly_test,
                account_service=self._account_service,
                on_complete=self.show_home,
                open_existing=open_existing,
            )
            return
        if self.route is UserRoute.ACTIVITY:
            self.activity = ActivityView(
                content,
                self._activity_service,
                ttk_module=self._ttk,
                go_home=self.show_home,
            )
            return
        self.home = HomeView(
            content,
            self._home_status,
            ttk_module=self._ttk,
            check_now=self._home_control.check_now,
            start=self._home_control.start,
            pause=self._home_control.pause,
            open_configuration=self.open_configuration,
            open_activity=self.show_activity,
        )

    def show_home(self) -> None:
        self.route = UserRoute.HOME
        self.first_run = None
        self._render()

    def open_configuration(self) -> None:
        self.route = UserRoute.FIRST_RUN
        self.home = None
        self._render(open_existing=True)

    def show_activity(self) -> None:
        self.route = UserRoute.ACTIVITY
        self.home = None
        self._render()

    def minimize(self) -> None:
        self.root.iconify()

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
        activity_service=ActivityService(paths.data_dir / "state.db"),
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
