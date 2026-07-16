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
from ..application.settings import DisabledStartupAdapter, SettingsService
from ..application.bucoliche_startup import (
    BucolicheStartupService,
    ExistingBucolicheGateway,
    WindowsAutomaticControlGateway,
)
from ..application.windows_startup import WindowsStartupAdapter
from ..application.windows_credentials import create_account_credential_service
from ..application_paths import default_application_paths
from .home import HomeView, StaticHomeStatusService
from .activity import ActivitySource, ActivityView, EmptyActivitySource
from .navigation import UserRoute, initial_route
from .settings import SettingsView
from .bucoliche_startup import BucolicheStartupView
from .wizard import AccountForm, FirstRunController


WINDOW_TITLE = "Caronte"
USER_VIEWS = (
    "Primo avvio", "Home", "Attivita e problemi", "Impostazioni",
    "Bucoliche e avvio",
)

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
        settings_service: SettingsService | None = None,
        bucoliche_startup_service: BucolicheStartupService | None = None,
    ) -> None:
        self.root = root
        self._ttk = ttk_module
        self._readonly_test = readonly_test
        self._account_service = account_service
        self._settings_service = settings_service or SettingsService(
            configuration, DisabledStartupAdapter()
        )
        self._bucoliche_startup_service = bucoliche_startup_service
        self._minimize_on_close = False
        interval_seconds = 300
        if configuration.exists() and settings_service is not None:
            current_settings = self._settings_service.load()
            self._minimize_on_close = current_settings.minimize_on_close
            interval_seconds = current_settings.interval_minutes * 60
        self._home_control = home_control or HomeRunController(
            configuration.store.source,
            ManagedOperationRunner(),
            interval_seconds=interval_seconds,
        )
        self.route = initial_route(configuration)
        self.root.title(WINDOW_TITLE)
        self.root.minsize(720, 480)
        self.current_frame: Any | None = None
        self.first_run: FirstRunController | None = None
        self.home: HomeView | None = None
        self.activity: ActivityView | None = None
        self.settings: SettingsView | None = None
        self.bucoliche_startup: BucolicheStartupView | None = None
        self._activity_service = activity_service or EmptyActivitySource()
        self._home_status = home_status or (
            AccountHomeStatusService(account_service)
            if account_service is not None
            else StaticHomeStatusService(HomeStatus("Pronto", 0))
        )
        self._render()
        if hasattr(self.root, "protocol"):
            self.root.protocol("WM_DELETE_WINDOW", self.close_window)

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
        if self.route is UserRoute.SETTINGS:
            self.settings = SettingsView(
                content,
                self._settings_service,
                ttk_module=self._ttk,
                go_home=self.show_home,
                on_saved=self._apply_settings,
            )
            return
        if self.route is UserRoute.BUCOLICHE_STARTUP:
            self.bucoliche_startup = BucolicheStartupView(
                content,
                self._bucoliche_startup_service,
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
            open_settings=self.show_settings,
            open_bucoliche_startup=self.show_bucoliche_startup,
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

    def show_settings(self) -> None:
        self.route = UserRoute.SETTINGS
        self.home = None
        self._render()

    def show_bucoliche_startup(self) -> None:
        self.route = UserRoute.BUCOLICHE_STARTUP
        self.home = None
        self._render()

    def _apply_settings(self, interval_seconds: int, minimize_on_close: bool) -> None:
        self._home_control.set_interval_seconds(interval_seconds)
        self._minimize_on_close = minimize_on_close

    def minimize(self) -> None:
        self.root.iconify()

    def close(self) -> None:
        """Stop the owned worker before closing the window."""

        self._home_control.close()
        self.root.destroy()

    def close_window(self) -> None:
        if self._minimize_on_close:
            self.minimize()
            return
        self.close()


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
        settings_service=SettingsService(
            configuration, WindowsStartupAdapter(configuration.store.source)
        ),
        bucoliche_startup_service=BucolicheStartupService(
            configuration,
            ExistingBucolicheGateway(configuration.store.source),
            WindowsAutomaticControlGateway(configuration),
        ),
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
